#!/usr/bin/env python3
"""
Download and verify GLiNER model for offline inference.
Called during Docker build. Not needed at runtime.
"""
import argparse
import logging
import os
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_and_verify(model_id: str, cache_dir: str) -> None:
    os.environ["HF_HOME"] = cache_dir

    from gliner import GLiNER

    logger.info(f"Downloading {model_id}...")
    model = GLiNER.from_pretrained(
        model_id,
        cache_dir=cache_dir,
        local_files_only=False,
    )
    logger.info("Model downloaded successfully.")

    # Verify offline loading works
    logger.info("Verifying offline load...")
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"
    test_model = GLiNER.from_pretrained(
        model_id,
        cache_dir=cache_dir,
        local_files_only=True,
    )

    # Smoke-test inference
    logger.info("Running inference smoke test...")
    result = test_model.predict_entities(
        "Test: 10.0.0.1 - Mario Rossi - Acme Corp",
        ["person name", "IP address", "organization name"],
    )
    logger.info(
        f"Verification passed. Test entities: "
        f"{[r['text'] for r in result]}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download and verify GLiNER model for offline use."
    )
    parser.add_argument("--model_id", required=True)
    parser.add_argument("--cache_dir", required=True)
    args = parser.parse_args()
    try:
        download_and_verify(args.model_id, args.cache_dir)
    except Exception:
        logger.exception("Model download/verification failed")
        sys.exit(1)
