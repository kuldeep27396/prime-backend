"""
Test script for technical assessment functionality
"""

import asyncio
import json
from app.services.assessment_service import assessment_service
from app.schemas.assessment import (
    AssessmentCreate, AssessmentType, CodingQuestionCreate, 
    ProgrammingLanguage, TestCase, CodeSubmission
)


async def test_judge0_execution():
    """Test Judge0 code execution"""
    print("Testing Judge0 code execution...")
    
    # Test Python code
    test_cases = [
        TestCase(input="5", expected_output="25", is_hidden=False),
        TestCase(input="3", expected_output="9", is_hidden=False),
        TestCase(input="0", expected_output="0", is_hidden=True)
    ]
    
    python_code = """
n = int(input())
print(n * n)
"""
    
    try:
        result = await assessment_service.code_executor.execute_code(
            code=python_code,
            language=ProgrammingLanguage.PYTHON,
            test_cases=test_cases,
            timeout=10
        )
        
        print(f"Execution successful: {result.success}")
        print(f"Output: {result.output}")
        print(f"Execution time: {result.execution_time:.3f}s")
        
        if result.test_results:
            print("\nTest Results:")
            for i, test_result in enumerate(result.test_results):
                status = "✅ PASSED" if test_result['passed'] else "❌ FAILED"
                print(f"  Test {i+1}: {status}")
                if not test_result.get('is_hidden', False):
                    print(f"    Input: {test_result['input']}")
                    print(f"    Expected: {test_result['expected_output']}")
                    print(f"    Got: {test_result['actual_output']}")
                if 'error' in test_result:
                    print(f"    Error: {test_result['error']}")
        
        if result.error:
            print(f"Error: {result.error}")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")


async def test_javascript_execution():
    """Test JavaScript code execution"""
    print("\n" + "="*50)
    print("Testing JavaScript code execution...")
    
    test_cases = [
        TestCase(input="hello world", expected_output="HELLO WORLD", is_hidden=False),
        TestCase(input="python", expected_output="PYTHON", is_hidden=False)
    ]
    
    js_code = """
const readline = require('readline');
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

rl.on('line', (input) => {
  console.log(input.toUpperCase());
  rl.close();
});
"""
    
    try:
        result = await assessment_service.code_executor.execute_code(
            code=js_code,
            language=ProgrammingLanguage.JAVASCRIPT,
            test_cases=test_cases,
            timeout=10
        )
        
        print(f"Execution successful: {result.success}")
        print(f"Output: {result.output}")
        print(f"Execution time: {result.execution_time:.3f}s")
        
        if result.test_results:
            print("\nTest Results:")
            for i, test_result in enumerate(result.test_results):
                status = "✅ PASSED" if test_result['passed'] else "❌ FAILED"
                print(f"  Test {i+1}: {status}")
                print(f"    Input: {test_result['input']}")
                print(f"    Expected: {test_result['expected_output']}")
                print(f"    Got: {test_result['actual_output']}")
                if 'error' in test_result:
                    print(f"    Error: {test_result['error']}")
        
        if result.error:
            print(f"Error: {result.error}")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")


async def test_compilation_error():
    """Test handling of compilation errors"""
    print("\n" + "="*50)
    print("Testing compilation error handling...")
    
    test_cases = [
        TestCase(input="5", expected_output="25", is_hidden=False)
    ]
    
    # Invalid Python code with syntax error
    invalid_code = """
n = int(input()
print(n * n  # Missing closing parentheses
"""
    
    try:
        result = await assessment_service.code_executor.execute_code(
            code=invalid_code,
            language=ProgrammingLanguage.PYTHON,
            test_cases=test_cases,
            timeout=10
        )
        
        print(f"Execution successful: {result.success}")
        print(f"Output: {result.output}")
        
        if result.test_results:
            print("\nTest Results:")
            for i, test_result in enumerate(result.test_results):
                status = "✅ PASSED" if test_result['passed'] else "❌ FAILED"
                print(f"  Test {i+1}: {status}")
                if 'error' in test_result:
                    print(f"    Error: {test_result['error']}")
        
        if result.error:
            print(f"Error: {result.error}")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")


async def test_timeout_handling():
    """Test timeout handling"""
    print("\n" + "="*50)
    print("Testing timeout handling...")
    
    test_cases = [
        TestCase(input="", expected_output="", is_hidden=False, timeout=2)
    ]
    
    # Code that runs infinitely
    infinite_code = """
while True:
    pass
"""
    
    try:
        result = await assessment_service.code_executor.execute_code(
            code=infinite_code,
            language=ProgrammingLanguage.PYTHON,
            test_cases=test_cases,
            timeout=3
        )
        
        print(f"Execution successful: {result.success}")
        print(f"Output: {result.output}")
        
        if result.test_results:
            print("\nTest Results:")
            for i, test_result in enumerate(result.test_results):
                status = "✅ PASSED" if test_result['passed'] else "❌ FAILED"
                print(f"  Test {i+1}: {status}")
                if 'error' in test_result:
                    print(f"    Error: {test_result['error']}")
        
        if result.error:
            print(f"Error: {result.error}")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")


async def test_multiple_languages():
    """Test multiple programming languages"""
    print("\n" + "="*50)
    print("Testing multiple programming languages...")
    
    test_cases = [
        TestCase(input="10", expected_output="55", is_hidden=False)
    ]
    
    # Sum of numbers from 1 to n
    codes = {
        ProgrammingLanguage.PYTHON: """
n = int(input())
total = sum(range(1, n + 1))
print(total)
""",
        ProgrammingLanguage.JAVA: """
import java.util.Scanner;

public class Solution {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        int n = scanner.nextInt();
        int total = 0;
        for (int i = 1; i <= n; i++) {
            total += i;
        }
        System.out.println(total);
        scanner.close();
    }
}
""",
        ProgrammingLanguage.CPP: """
#include <iostream>
using namespace std;

int main() {
    int n;
    cin >> n;
    int total = 0;
    for (int i = 1; i <= n; i++) {
        total += i;
    }
    cout << total << endl;
    return 0;
}
"""
    }
    
    for language, code in codes.items():
        print(f"\nTesting {language.value}...")
        try:
            result = await assessment_service.code_executor.execute_code(
                code=code,
                language=language,
                test_cases=test_cases,
                timeout=10
            )
            
            print(f"  Execution successful: {result.success}")
            if result.test_results:
                for i, test_result in enumerate(result.test_results):
                    status = "✅ PASSED" if test_result['passed'] else "❌ FAILED"
                    print(f"  Test {i+1}: {status}")
                    if not test_result['passed']:
                        print(f"    Expected: {test_result['expected_output']}")
                        print(f"    Got: {test_result['actual_output']}")
            
            if result.error:
                print(f"  Error: {result.error}")
                
        except Exception as e:
            print(f"  Test failed: {str(e)}")


async def main():
    """Run all tests"""
    print("Starting Technical Assessment Tests")
    print("=" * 50)
    
    await test_judge0_execution()
    await test_javascript_execution()
    await test_compilation_error()
    await test_timeout_handling()
    await test_multiple_languages()
    
    print("\n" + "="*50)
    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())