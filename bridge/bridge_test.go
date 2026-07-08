package main

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/betterleaks/betterleaks/sources"
)

const inlineConfigTOML = `
[[rules]]
id = "inline-config"
description = "Inline config fixture"
regex = "INLINE_CONFIG_[A-Z0-9]{16}"
keywords = ["INLINE_CONFIG_"]
`

func TestLoadConfigFromInlineTOML(t *testing.T) {
	cfg, err := loadConfig(scanRequest{ConfigTOML: stringPtr(inlineConfigTOML)})
	if err != nil {
		t.Fatalf("loadConfig returned error: %v", err)
	}
	if cfg.Path != "<pybetterleaks-inline-config>" {
		t.Fatalf("cfg.Path = %q, want inline sentinel path", cfg.Path)
	}
	if _, ok := cfg.Rules["inline-config"]; !ok {
		t.Fatal("inline rule was not parsed")
	}
}

func TestLoadConfigRejectsInlineTOMLAndPath(t *testing.T) {
	_, err := loadConfig(scanRequest{
		ConfigPath: stringPtr("betterleaks.toml"),
		ConfigTOML: stringPtr(inlineConfigTOML),
	})
	if err == nil {
		t.Fatal("loadConfig accepted config_toml with config_path")
	}
}

func TestFindGitRoot(t *testing.T) {
	repo := t.TempDir()
	if err := os.Mkdir(filepath.Join(repo, ".git"), 0o755); err != nil {
		t.Fatal(err)
	}
	nested := filepath.Join(repo, "src", "pkg")
	if err := os.MkdirAll(nested, 0o755); err != nil {
		t.Fatal(err)
	}

	got, err := findGitRoot(nested)
	if err != nil {
		t.Fatalf("findGitRoot returned error: %v", err)
	}
	if got != repo {
		t.Fatalf("findGitRoot = %q, want %q", got, repo)
	}
}

func TestGitWorktreeSkipFuncSkipsGitMetadata(t *testing.T) {
	repo := t.TempDir()
	skip := gitWorktreeSkipFunc(repo, nil)

	if !skip(map[string]string{sources.AttrPath: filepath.Join(repo, ".git", "config")}) {
		t.Fatal("expected .git/config to be skipped")
	}
	if skip(map[string]string{sources.AttrPath: filepath.Join(repo, ".gitignore")}) {
		t.Fatal("did not expect .gitignore to be skipped")
	}
}

func TestGitWorktreeSkipFuncPreservesBaseSkip(t *testing.T) {
	repo := t.TempDir()
	skip := gitWorktreeSkipFunc(repo, func(attrs map[string]string) bool {
		return attrs[sources.AttrPath] == filepath.Join(repo, "skip.txt")
	})

	if !skip(map[string]string{sources.AttrPath: filepath.Join(repo, "skip.txt")}) {
		t.Fatal("expected base skip to be preserved")
	}
}

func stringPtr(value string) *string {
	return &value
}
