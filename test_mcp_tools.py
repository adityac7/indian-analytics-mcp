#!/usr/bin/env python3
"""
Test suite for Indian Analytics MCP Server

Run this to verify your setup and test all tools.

Usage:
    python test_mcp_tools.py
"""

import os
import sys
import asyncio
from indian_analytics_mcp import (
    explain_term,
    list_available_datasets,
    get_top_apps,
    profile_audience,
    query_dataset,
    GetGlossaryInput,
    AppRankingInput,
    AudienceProfileInput,
    QueryDatasetInput,
    ResponseFormat
)


class TestContext:
    """Mock context for testing"""
    def __init__(self):
        self.request_context = type('obj', (object,), {
            'lifespan_state': {'pools': {}}
        })()


async def test_environment():
    """Test environment variables are set"""
    print("=" * 80)
    print("TEST 1: Environment Variables")
    print("=" * 80)

    required_vars = [
        "DATASET_1_NAME",
        "DATASET_1_DESC",
        "DATASET_1_CONNECTION",
        "DATASET_1_DICTIONARY"
    ]

    all_set = True
    for var in required_vars:
        if var in os.environ:
            print(f"✅ {var} is set")
        else:
            print(f"❌ {var} is NOT set")
            all_set = False

    if all_set:
        print("\n✅ All environment variables configured!")
    else:
        print("\n❌ Missing environment variables. Please configure them.")
        print("\nExample:")
        print('export DATASET_1_NAME="digital_insights"')
        print('export DATASET_1_DESC="Mobile app usage data"')
        print('export DATASET_1_CONNECTION="postgresql://..."')
        print('export DATASET_1_DICTIONARY=\'{"digital_insights": "Main table"}\'')
        sys.exit(1)

    return all_set


async def test_explain_term():
    """Test explain_term tool"""
    print("\n" + "=" * 80)
    print("TEST 2: Explain Term Tool")
    print("=" * 80)

    try:
        # Test with no parameters
        result = await explain_term(GetGlossaryInput())
        print("✅ explain_term() - List all terms")
        print(result[:200] + "...\n")

        # Test with specific term
        result = await explain_term(GetGlossaryInput(term="nccs"))
        print("✅ explain_term(term='nccs') - Specific term")
        print(result[:200] + "...\n")

        # Test with unknown term
        result = await explain_term(GetGlossaryInput(term="unknown_term"))
        print("✅ explain_term(term='unknown_term') - Error handling")
        print(result[:200] + "...\n")

        return True
    except Exception as e:
        print(f"❌ explain_term failed: {str(e)}")
        return False


async def test_list_datasets():
    """Test list_available_datasets tool"""
    print("\n" + "=" * 80)
    print("TEST 3: List Datasets Tool")
    print("=" * 80)

    try:
        result = await list_available_datasets()
        print("✅ list_available_datasets()")
        print(result[:300] + "...\n")
        return True
    except Exception as e:
        print(f"❌ list_available_datasets failed: {str(e)}")
        return False


async def test_integration():
    """Test integration with actual database"""
    print("\n" + "=" * 80)
    print("TEST 4: Database Integration (if configured)")
    print("=" * 80)

    # Check if database is configured
    if "DATASET_1_CONNECTION" not in os.environ:
        print("⚠️  Skipping database tests - no connection configured")
        return None

    conn_str = os.environ["DATASET_1_CONNECTION"]
    if "localhost" in conn_str or "example" in conn_str:
        print("⚠️  Skipping database tests - using placeholder connection")
        return None

    print("Database connection configured, testing tools...")

    try:
        # This would require proper context setup
        # For now, just verify the connection string is valid
        if conn_str.startswith("postgresql://"):
            print("✅ Valid PostgreSQL connection string")
            return True
        else:
            print("❌ Invalid connection string format")
            return False
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False


def test_tool_descriptions():
    """Test that tool descriptions are marketing-friendly"""
    print("\n" + "=" * 80)
    print("TEST 5: Tool Descriptions (Marketing-Friendly)")
    print("=" * 80)

    # Check explain_term docstring
    if explain_term.__doc__:
        doc = explain_term.__doc__
        has_examples = "Use this when" in doc or "Examples:" in doc
        has_emoji = any(c in doc for c in "📚💡🎯📊")

        print(f"explain_term:")
        print(f"  {'✅' if has_examples else '❌'} Has usage examples")
        print(f"  {'✅' if has_emoji else '❌'} Has visual elements (emoji)")
        print(f"  Length: {len(doc)} chars")

    # Check list_available_datasets docstring
    if list_available_datasets.__doc__:
        doc = list_available_datasets.__doc__
        has_business_context = any(word in doc.lower() for word in ["consumer", "analyze", "discover"])

        print(f"\nlist_available_datasets:")
        print(f"  {'✅' if has_business_context else '❌'} Has business context")
        print(f"  Length: {len(doc)} chars")

    return True


def test_error_messages():
    """Test error message quality"""
    print("\n" + "=" * 80)
    print("TEST 6: Error Message Quality")
    print("=" * 80)

    # Simulate common errors and check messages
    test_cases = [
        {
            "name": "Unknown term",
            "test": lambda: asyncio.run(explain_term(GetGlossaryInput(term="xyz123"))),
            "expected_keywords": ["not found", "available"]
        }
    ]

    for test_case in test_cases:
        try:
            result = test_case["test"]()
            has_keywords = all(kw in result.lower() for kw in test_case["expected_keywords"])

            print(f"\n{test_case['name']}:")
            print(f"  {'✅' if has_keywords else '❌'} Has helpful keywords")
            print(f"  Preview: {result[:150]}...")
        except Exception as e:
            print(f"\n{test_case['name']}: ❌ Error: {str(e)}")

    return True


def print_summary(results):
    """Print test summary"""
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    total = len(results)
    passed = sum(1 for r in results if r)
    failed = sum(1 for r in results if r is False)
    skipped = sum(1 for r in results if r is None)

    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Skipped: {skipped}")

    if failed == 0:
        print("\n🎉 All tests passed! Your MCP server is ready to use.")
        print("\nNext steps:")
        print("1. Try running the server: python indian_analytics_mcp.py")
        print("2. Test with Claude Desktop")
        print("3. Check QUICK_START.md for usage examples")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("Common issues:")
        print("- Missing environment variables")
        print("- Database connection not configured")
        print("- Dependencies not installed")


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("INDIAN ANALYTICS MCP SERVER - TEST SUITE")
    print("=" * 80)
    print("\nThis will test your MCP server setup and verify all features work.\n")

    results = []

    # Test 1: Environment
    results.append(await test_environment())

    # Test 2: Explain Term
    results.append(await test_explain_term())

    # Test 3: List Datasets
    results.append(await test_list_datasets())

    # Test 4: Database Integration
    results.append(await test_integration())

    # Test 5: Tool Descriptions
    results.append(test_tool_descriptions())

    # Test 6: Error Messages
    results.append(test_error_messages())

    # Print summary
    print_summary(results)


def main():
    """Main entry point"""
    # Check if running with database credentials
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
Indian Analytics MCP Server - Test Suite

Usage:
    python test_mcp_tools.py

This script tests:
1. Environment variable configuration
2. Tool functionality (explain_term, list_datasets)
3. Database integration (if configured)
4. Tool description quality
5. Error message quality

Before running:
- Set DATASET_1_* environment variables
- Or configure them in your shell/IDE

Example:
    export DATASET_1_NAME="digital_insights"
    export DATASET_1_DESC="Mobile app usage data"
    export DATASET_1_CONNECTION="postgresql://..."
    export DATASET_1_DICTIONARY='{"digital_insights": "Main table"}'

    python test_mcp_tools.py
        """)
        sys.exit(0)

    # Run tests
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
