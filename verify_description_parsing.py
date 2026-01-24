import asyncio
import re

# Mock job description to test parsing logic
mock_jobs = [
    {
        "role": "Python Developer",
        "description": "Job Title: Python Developer LLM NLP ... Experience: 5 Years ... Mandatory Skills: Python",
        "expected_exp": "5 years",
        "should_pass": False
    },
    {
        "role": "Junior AI",
        "description": "We are looking for a Junior AI Engineer with 0-2 years experience in Python.",
        "expected_exp": "0-2 years",
        "should_pass": True
    },
    {
        "role": "Senior Lead",
        "description": "Required: 8+ years experience in software development.",
        "expected_exp": "8+ years",
        "should_pass": False
    },
    {
        "role": "Implicit Exp",
        "description": "Must have 3 years of experience in ML.",
        "expected_exp": "3 years",
        "should_pass": False
    },
     {
        "role": "Range Exp",
        "description": "Experience: 1-3 Years",
        "expected_exp": "1-3 years",
        "should_pass": True
    }
]

async def verify_description_parsing():
    print("🔍 Testing Job Description Experience Extraction...\n")
    
    for job in mock_jobs:
        description = job["description"]
        print(f"Checking: {job['role']}")
        print(f"  Desc Snippet: '{description[:60]}...'")
        
        # --- NEW LOGIC REPLICATION FROM SCORING AGENT ---
        exp_req = ""
        
        # Pattern 1: "Experience: 5 Years"
        exp_match = re.search(r'experience\s*:\s*(\d+)(?:\s*-\s*(\d+))?\s*y', description.lower())
        
        # Pattern 2: "5 years experience" or "5-7 years experience"
        if not exp_match:
            exp_match = re.search(r'(\d+)(?:\s*-\s*(\d+))?\s*\+?\s*years?\s*experience', description.lower())
            
        if exp_match:
            min_e = int(exp_match.group(1))
            max_e = int(exp_match.group(2)) if exp_match.group(2) else None
            
            if max_e:
                exp_req = f"{min_e}-{max_e} years"
            else:
                exp_req = f"{min_e} years"
        
        print(f"  -> Extracted: '{exp_req}' (Expected: '{job['expected_exp']}')")
        
        # Verify filtering logic on extracted result
        # Re-using the logic from verify_agent_logic.py slightly modified for string input
        numbers = re.findall(r'\d+', exp_req)
        min_exp = int(numbers[0]) if numbers else 0
        
        passed = True
        if min_exp >= 3:
            passed = False
            
        print(f"  -> Passed Filter? {passed} (Expected: {job['should_pass']})")
        
        if passed != job['should_pass']:
            print("  ❌ FAILURE")
        else:
            print("  ✅ SUCCESS")
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(verify_description_parsing())
