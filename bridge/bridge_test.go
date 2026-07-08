package main

import "testing"

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

func stringPtr(value string) *string {
	return &value
}
