#!/usr/bin/env python3
"""
Gemini API Verification Script
Checks if your Gemini API key is valid and the API is reachable.
Uses the new `google-genai` SDK (google.genai).
"""

import sys
import time

# ── Config ────────────────────────────────────────────────────────────────────
# API_KEY = "AIzaSyAGmmcpth2doFj85JHzh6CpQG74R_8mB-8"
API_KEY = "AIzaSyAGmmcpth2doFj85JHzh6CpQG74R_8mB-8"
MODEL   = "gemini-1.5-flash"          # lightweight model — good for a health check
# ─────────────────────────────────────────────────────────────────────────────


def check_dependencies():
    try:
        import google.genai
        return True
    except ImportError:
        print("❌  'google-genai' package not found.")
        print("    Install it with:  pip install google-genai")
        sys.exit(1)


def verify_api_key():
    masked = API_KEY[:6] + "..." + API_KEY[-4:]
    print(f"🔑  API key found: {masked}")


def get_client():
    """Return a configured google.genai Client instance."""
    from google import genai
    return genai.Client(api_key=API_KEY)


def check_model_list():
    print("\n📋  Fetching available models …")
    try:
        client = get_client()
        models = [
            m.name
            for m in client.models.list()
            if m.supported_actions and "generateContent" in m.supported_actions
        ]
        print(f"    ✅  Found {len(models)} content-generation model(s).")
        for name in models[:5]:
            print(f"        • {name}")
        if len(models) > 5:
            print(f"        … and {len(models) - 5} more")
        return True
    except Exception as e:
        print(f"    ❌  Could not list models: {e}")
        return False


def send_test_prompt():
    print(f"\n🚀  Sending test prompt to '{MODEL}' …")
    prompt = "Reply with exactly one sentence: 'Gemini API is working correctly.'"

    try:
        client = get_client()
        start  = time.time()
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )
        elapsed = time.time() - start

        text = response.text.strip()
        print(f"    ✅  Response received in {elapsed:.2f}s")
        print(f"    💬  Model says: {text}")
        return True
    except Exception as e:
        print(f"    ❌  Generation failed: {e}")
        return False


def check_token_count():
    print(f"\n🔢  Checking token counting …")
    try:
        client = get_client()
        result = client.models.count_tokens(
            model=MODEL,
            contents="Hello, Gemini!",
        )
        print(f"    ✅  Token count API works  (sample count: {result.total_tokens})")
        return True
    except Exception as e:
        print(f"    ❌  Token count failed: {e}")
        return False


def print_summary(results: dict):
    print("\n" + "─" * 50)
    print("  VERIFICATION SUMMARY")
    print("─" * 50)
    all_ok = True
    for check, passed in results.items():
        icon = "✅" if passed else "❌"
        print(f"  {icon}  {check}")
        if not passed:
            all_ok = False
    print("─" * 50)
    if all_ok:
        print("  🎉  Gemini API is fully operational!\n")
    else:
        print("  ⚠️   Some checks failed. Review the output above.\n")


def main():
    print("=" * 50)
    print("  Gemini API Verification Script")
    print("=" * 50)

    check_dependencies()
    verify_api_key()

    results = {
        "Model listing":      check_model_list(),
    }

    print_summary(results)
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()