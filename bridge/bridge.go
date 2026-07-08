package main

/*
#include <stdlib.h>
*/
import "C"

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"runtime/debug"
	"sync"
	"time"
	"unsafe"

	"github.com/betterleaks/betterleaks/config"
	"github.com/betterleaks/betterleaks/detect"
	"github.com/betterleaks/betterleaks/report"
	"github.com/betterleaks/betterleaks/sources"
)

const bundledBetterleaksVersion = "v1.6.1"

const (
	defaultMaxDecodeDepth  = 5
	defaultMaxArchiveDepth = 8
)

type scanRequest struct {
	Mode              string            `json:"mode"`
	Target            string            `json:"target"`
	RequestID         *string           `json:"request_id,omitempty"`
	ConfigPath        *string           `json:"config_path,omitempty"`
	Validation        bool              `json:"validation"`
	ValidationEnvVars []string          `json:"validation_env_vars,omitempty"`
	ValidationEnv     map[string]string `json:"validation_env,omitempty"`
	Redact            bool              `json:"redact"`
	TimeoutSeconds    *float64          `json:"timeout_seconds,omitempty"`
}

type scanResponse struct {
	OK                 bool          `json:"ok"`
	BetterleaksVersion string        `json:"betterleaks_version"`
	Findings           []finding     `json:"findings"`
	Errors             []bridgeError `json:"errors"`
}

type bridgeError struct {
	Code    string `json:"code"`
	Message string `json:"message"`
	Detail  string `json:"detail,omitempty"`
}

type finding struct {
	RuleID           string            `json:"rule_id"`
	Description      string            `json:"description,omitempty"`
	File             string            `json:"file,omitempty"`
	Line             int               `json:"line,omitempty"`
	Column           int               `json:"column,omitempty"`
	EndLine          int               `json:"end_line,omitempty"`
	EndColumn        int               `json:"end_column,omitempty"`
	Secret           string            `json:"secret,omitempty"`
	Match            string            `json:"match,omitempty"`
	ValidationStatus string            `json:"validation_status,omitempty"`
	ValidationMeta   map[string]any    `json:"validation_meta,omitempty"`
	Tags             []string          `json:"tags,omitempty"`
	Attributes       map[string]string `json:"attributes,omitempty"`
	Raw              map[string]any    `json:"raw,omitempty"`
}

var activeScans = struct {
	sync.Mutex
	cancels map[string]context.CancelFunc
}{
	cancels: make(map[string]context.CancelFunc),
}

var validationEnvMu sync.Mutex

//export BetterleaksScanJSON
func BetterleaksScanJSON(requestJSON *C.char) (response *C.char) {
	defer func() {
		if recovered := recover(); recovered != nil {
			response = jsonCString(scanResponse{
				OK:                 false,
				BetterleaksVersion: bundledBetterleaksVersion,
				Findings:           []finding{},
				Errors: []bridgeError{{
					Code:    "panic",
					Message: "Betterleaks bridge panicked",
					Detail:  panicDetail(recovered),
				}},
			})
		}
	}()

	if requestJSON == nil {
		return jsonCString(errorResponse("invalid_request", "request JSON pointer was NULL", ""))
	}

	var req scanRequest
	if err := json.Unmarshal([]byte(C.GoString(requestJSON)), &req); err != nil {
		return jsonCString(errorResponse("invalid_json", "failed to decode request JSON", err.Error()))
	}

	resp := runScan(req)
	return jsonCString(resp)
}

//export BetterleaksCancel
func BetterleaksCancel(requestID *C.char) (response *C.char) {
	defer func() {
		if recovered := recover(); recovered != nil {
			response = jsonCString(scanResponse{
				OK:                 false,
				BetterleaksVersion: bundledBetterleaksVersion,
				Findings:           []finding{},
				Errors: []bridgeError{{
					Code:    "panic",
					Message: "Betterleaks cancel bridge panicked",
					Detail:  panicDetail(recovered),
				}},
			})
		}
	}()

	if requestID == nil {
		return jsonCString(errorResponse("invalid_request", "request id pointer was NULL", ""))
	}

	id := C.GoString(requestID)
	if id == "" {
		return jsonCString(errorResponse("invalid_request", "request id was empty", ""))
	}

	activeScans.Lock()
	cancel, ok := activeScans.cancels[id]
	activeScans.Unlock()
	if !ok {
		return jsonCString(errorResponse("scan_not_found", "scan request id is not active", id))
	}

	cancel()
	return jsonCString(scanResponse{
		OK:                 true,
		BetterleaksVersion: bundledBetterleaksVersion,
		Findings:           []finding{},
		Errors:             []bridgeError{},
	})
}

//export BetterleaksVersion
func BetterleaksVersion() *C.char {
	return C.CString(bundledBetterleaksVersion)
}

//export BetterleaksFree
func BetterleaksFree(ptr *C.char) {
	C.free(unsafe.Pointer(ptr))
}

func runScan(req scanRequest) scanResponse {
	ctx, cancel, err := contextFromRequest(req)
	if err != nil {
		return errorResponse("invalid_timeout", "invalid scan timeout", err.Error())
	}
	defer cancel()
	if err := registerScan(req, cancel); err != nil {
		return errorResponse("invalid_request", "failed to register scan request", err.Error())
	}
	defer unregisterScan(req)
	restoreEnv := applyValidationEnv(req)
	defer restoreEnv()

	switch req.Mode {
	case "text":
		return scanText(ctx, req)
	case "dir":
		return scanDir(ctx, req)
	default:
		return errorResponse("unsupported_mode", "unsupported scan mode", req.Mode)
	}
}

type envRestore struct {
	name    string
	value   string
	existed bool
}

func applyValidationEnv(req scanRequest) func() {
	if !req.Validation {
		return func() {}
	}

	names := validationEnvVars(req)
	if len(names) == 0 {
		return func() {}
	}

	validationEnvMu.Lock()
	restore := make([]envRestore, 0, len(names))
	for _, name := range names {
		oldValue, existed := os.LookupEnv(name)
		restore = append(restore, envRestore{name: name, value: oldValue, existed: existed})
		if value, ok := req.ValidationEnv[name]; ok {
			_ = os.Setenv(name, value)
		} else {
			_ = os.Unsetenv(name)
		}
	}

	return func() {
		for i := len(restore) - 1; i >= 0; i-- {
			item := restore[i]
			if item.existed {
				_ = os.Setenv(item.name, item.value)
			} else {
				_ = os.Unsetenv(item.name)
			}
		}
		validationEnvMu.Unlock()
	}
}

func registerScan(req scanRequest, cancel context.CancelFunc) error {
	if req.RequestID == nil || *req.RequestID == "" {
		return nil
	}

	activeScans.Lock()
	defer activeScans.Unlock()
	if _, exists := activeScans.cancels[*req.RequestID]; exists {
		return fmt.Errorf("request id is already active: %s", *req.RequestID)
	}
	activeScans.cancels[*req.RequestID] = cancel
	return nil
}

func unregisterScan(req scanRequest) {
	if req.RequestID == nil || *req.RequestID == "" {
		return
	}

	activeScans.Lock()
	delete(activeScans.cancels, *req.RequestID)
	activeScans.Unlock()
}

func contextFromRequest(req scanRequest) (context.Context, context.CancelFunc, error) {
	if req.TimeoutSeconds == nil {
		ctx, cancel := context.WithCancel(context.Background())
		return ctx, cancel, nil
	}
	if *req.TimeoutSeconds <= 0 {
		return nil, nil, errors.New("timeout_seconds must be greater than zero")
	}
	timeout := time.Duration(*req.TimeoutSeconds * float64(time.Second))
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	return ctx, cancel, nil
}

func scanText(ctx context.Context, req scanRequest) scanResponse {
	detector, err := newDetector(ctx, req)
	if err != nil {
		return errorResponse("detector_init_failed", "failed to initialize Betterleaks detector", err.Error())
	}

	return scanSource(ctx, req, detector, textSource{content: req.Target}, "text_scan_failed")
}

func scanDir(ctx context.Context, req scanRequest) scanResponse {
	info, err := os.Stat(req.Target)
	if err != nil {
		return errorResponse("target_stat_failed", "failed to inspect scan target", err.Error())
	}
	if !info.IsDir() {
		return errorResponse("target_not_directory", "scan_dir target is not a directory", req.Target)
	}

	detector, err := newDetector(ctx, req)
	if err != nil {
		return errorResponse("detector_init_failed", "failed to initialize Betterleaks detector", err.Error())
	}

	source := &sources.Files{
		ShouldSkip:      detector.SkipFunc(),
		FollowSymlinks:  detector.FollowSymlinks,
		MaxFileSize:     detector.MaxTargetMegaBytes * 1_000_000,
		Path:            req.Target,
		Sema:            detector.Sema,
		MaxArchiveDepth: detector.MaxArchiveDepth,
	}
	return scanSource(ctx, req, detector, source, "directory_scan_failed")
}

type textSource struct {
	content string
}

func (s textSource) Fragments(ctx context.Context, yield sources.FragmentsFunc) error {
	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
		return yield(sources.Fragment{Raw: s.content}, nil)
	}
}

func scanSource(
	ctx context.Context,
	req scanRequest,
	detector *detect.Detector,
	source sources.Source,
	errorCode string,
) scanResponse {
	rawFindings := []report.Finding{}
	var scanErr error

	for result := range detector.Run(ctx, source) {
		if result.Err != nil {
			scanErr = result.Err
			break
		}
		rawFindings = append(rawFindings, result.Finding)
	}

	if err := ctx.Err(); err != nil {
		return errorResponse("scan_timeout", "scan timed out", err.Error())
	}
	if scanErr != nil {
		return errorResponse(errorCode, "failed to scan target", scanErr.Error())
	}

	if req.Redact {
		detect.RedactFindings(rawFindings, 100)
	}
	return findingsResponse(rawFindings, "")
}

func newDetector(ctx context.Context, req scanRequest) (*detect.Detector, error) {
	cfg, err := loadConfig(req)
	if err != nil {
		return nil, err
	}

	detector := detect.NewDetectorContext(ctx, cfg, detect.ValidationOptions{
		Enabled:           req.Validation,
		Timeout:           validationTimeout(req),
		ValidationEnvVars: validationEnvVars(req),
	})
	detector.MaxDecodeDepth = defaultMaxDecodeDepth
	detector.MaxArchiveDepth = defaultMaxArchiveDepth
	detector.MaxTargetMegaBytes = 0
	detector.SkipFindingAppend = true
	if req.Redact {
		detector.Redact = 100
	}
	return detector, nil
}

func validationEnvVars(req scanRequest) []string {
	seen := make(map[string]struct{}, len(req.ValidationEnvVars)+len(req.ValidationEnv))
	values := make([]string, 0, len(req.ValidationEnvVars)+len(req.ValidationEnv))
	for _, name := range req.ValidationEnvVars {
		if _, ok := seen[name]; ok {
			continue
		}
		seen[name] = struct{}{}
		values = append(values, name)
	}
	for name := range req.ValidationEnv {
		if _, ok := seen[name]; ok {
			continue
		}
		seen[name] = struct{}{}
		values = append(values, name)
	}
	return values
}

func loadConfig(req scanRequest) (*config.Config, error) {
	if req.ConfigPath != nil && *req.ConfigPath != "" {
		return config.LoadFile(*req.ConfigPath)
	}
	return config.Default()
}

func findingsResponse(rawFindings []report.Finding, file string) scanResponse {
	findings := make([]finding, 0, len(rawFindings))
	for _, rawFinding := range rawFindings {
		findings = append(findings, convertFinding(rawFinding, file))
	}

	return scanResponse{
		OK:                 true,
		BetterleaksVersion: bundledBetterleaksVersion,
		Findings:           findings,
		Errors:             []bridgeError{},
	}
}

func convertFinding(raw report.Finding, fallbackFile string) finding {
	file := raw.File
	if file == "" {
		file = fallbackFile
	}
	attributes := map[string]string{}
	for key, value := range raw.Attributes {
		attributes[key] = value
	}
	if raw.Fingerprint != "" {
		attributes["fingerprint"] = raw.Fingerprint
	}
	if raw.Entropy != 0 {
		attributes["entropy"] = fmt.Sprintf("%f", raw.Entropy)
	}

	return finding{
		RuleID:           raw.RuleID,
		Description:      raw.Description,
		File:             file,
		Line:             raw.StartLine,
		Column:           raw.StartColumn,
		EndLine:          raw.EndLine,
		EndColumn:        raw.EndColumn,
		Secret:           raw.Secret,
		Match:            raw.Match,
		ValidationStatus: string(raw.ValidationStatus),
		ValidationMeta:   raw.ValidationMeta,
		Tags:             raw.Tags,
		Attributes:       attributes,
		Raw: map[string]any{
			"fingerprint":        raw.Fingerprint,
			"entropy":            raw.Entropy,
			"commit":             raw.Commit,
			"author":             raw.Author,
			"email":              raw.Email,
			"date":               raw.Date,
			"message":            raw.Message,
			"validation_reason":  raw.ValidationReason,
			"capture_groups":     raw.CaptureGroups,
			"rule_specificity":   raw.RuleSpecificity,
			"validation_status":  string(raw.ValidationStatus),
			"validation_meta":    raw.ValidationMeta,
			"match_context":      raw.MatchContext,
			"deprecated_file":    raw.File,
			"deprecated_symlink": raw.SymlinkFile,
		},
	}
}

func errorResponse(code string, message string, detail string) scanResponse {
	return scanResponse{
		OK:                 false,
		BetterleaksVersion: bundledBetterleaksVersion,
		Findings:           []finding{},
		Errors: []bridgeError{{
			Code:    code,
			Message: message,
			Detail:  detail,
		}},
	}
}

func jsonCString(resp scanResponse) *C.char {
	raw, err := json.Marshal(resp)
	if err != nil {
		raw = []byte(`{"ok":false,"betterleaks_version":"v1.6.1","findings":[],"errors":[{"code":"json_encode_failed","message":"failed to encode native response"}]}`)
	}
	return C.CString(string(raw))
}

func validationTimeout(req scanRequest) time.Duration {
	if req.TimeoutSeconds == nil || *req.TimeoutSeconds <= 0 {
		return 0
	}
	return time.Duration(*req.TimeoutSeconds * float64(time.Second))
}

func panicDetail(recovered any) string {
	detail := fmt.Sprintf("%v", recovered)
	if os.Getenv("PYBETTERLEAKS_DEBUG_NATIVE") == "1" {
		return fmt.Sprintf("%s\n%s", detail, string(debug.Stack()))
	}
	return detail
}

func main() {}
