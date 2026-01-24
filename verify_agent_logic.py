import asyncio
import re

# Mock job data based on USER'S EXACT REQUEST
# "more than 2 years pls dont retreive it" -> Interpreted as Min <= 2 (as 2-4 is allowed)

mock_jobs = [
    # --- SHOULD PASS (User's List) ---
    {"role": "Fresher Role", "company": "A", "experience_required": "Fresher", "should_pass": True},
    {"role": "0 Years", "company": "B", "experience_required": "0 years", "should_pass": True},
    {"role": "0-1 Years", "company": "C", "experience_required": "0-1 years", "should_pass": True},
    {"role": "0-2 Years", "company": "D", "experience_required": "0-2 years", "should_pass": True},
    {"role": "1-2 Years", "company": "E", "experience_required": "1-2 years", "should_pass": True},
    {"role": "1-3 Years", "company": "F", "experience_required": "1-3 years", "should_pass": True},
    {"role": "2-3 Years", "company": "G", "experience_required": "2-3 years", "should_pass": True},
    {"role": "2-4 Years", "company": "H", "experience_required": "2-4 years", "should_pass": True},
    
    # --- SHOULD FAIL (Too Senior) ---
    {"role": "3+ Years", "company": "X", "experience_required": "3+ years", "should_pass": False},
    {"role": "3-5 Years", "company": "Y", "experience_required": "3-5 years", "should_pass": False},
    {"role": "4 Years", "company": "Z", "experience_required": "4 years", "should_pass": False},
    
    # --- SHOULD FAIL (Max too high?) ---
    # User didn't list 2-5, so we assume fail based on "more than 2" strictness
    {"role": "2-5 Years", "company": "Q", "experience_required": "2-5 years", "should_pass": False},
]

async def verify_exact_ranges():
    print("🔍 Testing User's Exact Experience Ranges...\n")
    
    for job in mock_jobs:
        exp_req = job["experience_required"]
        should_pass = job["should_pass"]
        
        # --- LOGIC REPLICATION (from base_discovery_agent.py) ---
        matches = re.findall(r'(\d+)\s*(?:-|\s*to\s*|\s*)\s*(\d*)', exp_req.lower())
        
        min_exp = 0
        max_exp = 0
        found_valid = False
        
        if matches:
            valid_matches = []
            for m in matches:
                n1 = int(m[0])
                n2 = int(m[1]) if m[1] else n1
                if n1 < 20 and n2 < 20: 
                    valid_matches.append((n1, n2))
            
            if valid_matches:
                min_exp = valid_matches[0][0]
                max_exp = valid_matches[0][1]
                found_valid = True
        
        if not found_valid:
            # Fallback checks (Fresher, etc)
            if "fresher" in exp_req.lower() or "0 years" in exp_req.lower():
                min_exp = 0
                max_exp = 0
            elif "4 years" in exp_req.lower(): # Specific exclusion test logic
                # logic only parses regex. 4 years -> min=4, max=4
                simple = re.findall(r'\d+', exp_req)
                if simple:
                    min_exp = int(simple[0])
                    max_exp = int(simple[0])
        
        status = True
        reason = "OK"
        
        # RULES:
        if min_exp >= 3:
            status = False
            reason = "Min >= 3"
        elif max_exp >= 5 and max_exp > 0: # Check max cap
            status = False
            reason = "Max >= 5"
        
        # Verify
        result_icon = "✅" if status == should_pass else "❌ FAILURE"
        print(f"Checking '{exp_req}' -> Min:{min_exp} Max:{max_exp} -> Pass: {status} ({reason}) | {result_icon}")
        
    print("-" * 30)

if __name__ == "__main__":
    asyncio.run(verify_exact_ranges())
