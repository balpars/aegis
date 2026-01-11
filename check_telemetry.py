#!/usr/bin/env python3
"""Test telemetry collection for HuggingFace models."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from aegis.models.registry import ModelRegistryV2
from aegis.models.runtime_manager import DEFAULT_RUNTIME_MANAGER

def test_telemetry():
    """Test telemetry collection for HF models."""
    print("=" * 60)
    print("AEGIS TELEMETRY TEST")
    print("=" * 60)

    registry = ModelRegistryV2()

    # Get HF models
    all_models = registry.list_models()
    hf_models = []
    for m in all_models:
        model_type = m.model_type.value if hasattr(m.model_type, 'value') else str(m.model_type)
        if model_type.startswith("hf_"):
            hf_models.append(m)

    if not hf_models:
        print("\n[!] No HuggingFace models found in registry!")
        print("    Add HF models via the Models page first.")
        return

    print(f"\n[+] Found {len(hf_models)} HuggingFace model(s):\n")

    for model in hf_models[:2]:  # Test first 2
        model_type = m.model_type.value if hasattr(m.model_type, 'value') else str(m.model_type)
        print(f"[*] Model: {model.model_name}")
        print(f"    ID: {model.model_id}")
        print(f"    Type: {model_type}")
        print(f"    Enabled: {model.enabled}")

        if not model.enabled:
            print("    [!] Model disabled, skipping...\n")
            continue

        try:
            print("    [~] Loading model runtime...")
            runtime = DEFAULT_RUNTIME_MANAGER.get_runtime(model)

            print("    [+] Runtime loaded!")
            print(f"    [T] Load time: {runtime.provider_load_time_ms}ms")

            if runtime.telemetry:
                print("\n    [TELEMETRY DATA]:")
                for key, value in runtime.telemetry.items():
                    if value:
                        if key == "device":
                            marker = "[GPU]" if "cuda" in str(value).lower() else "[MPS]" if "mps" in str(value).lower() else "[CPU]"
                            print(f"      {marker} {key}: {value}")
                        elif key == "vram_mb" and value > 0:
                            print(f"      [MEM] {key}: {value}MB")
                        elif key == "quantization":
                            print(f"      [QNT] {key}: {value}")
                        elif key == "precision":
                            print(f"      [PRC] {key}: {value}")
                        else:
                            print(f"      [ - ] {key}: {value}")
            else:
                print("    [!] No telemetry data collected")

            # Clean up
            runtime.close()
            DEFAULT_RUNTIME_MANAGER.clear_model(model.model_id)

        except Exception as e:
            print(f"    [X] Error: {e}")

        print()

    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_telemetry()
