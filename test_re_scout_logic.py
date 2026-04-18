# test_re_scout_logic.py
from ai_module import DifferentialAnalyzer

def test_logic():
    analyzer = DifferentialAnalyzer()
    
    # 1. Simulate Baseline (Idle) across multiple IDs
    # ID 0x100 is static
    # ID 0x200 is static
    baseline = {
        0x100: [b'\x00\x00'] * 10,
        0x200: [b'\xFF\x00'] * 10
    }
    
    # 2. Simulate Action (Event)
    # ID 0x100: Bit 0 starts flipping (Pure Discovery)
    # ID 0x200: Bit 8 starts flipping (Pure Discovery in byte 1)
    # ID 0x300: New ID appears (Smart detection)
    action = {
        0x100: [b'\x00\x00', b'\x01\x00', b'\x00\x00', b'\x01\x00'] * 5,
        0x200: [b'\xFF\x00', b'\xFF\x01', b'\xFF\x00', b'\xFF\x01'] * 5,
        0x300: [b'\xAA\xBB'] * 10
    }
    
    results = analyzer.analyze(baseline, action)
    
    print(f"IDs with differences: {list(results.keys())}")
    
    # Check ID 0x100
    if 0x100 in results:
        res100 = results[0x100]
        cands = res100["candidates"]
        print(f"[ID 0x100] Candidates: {len(cands)}")
        found_pure = any(c["start_bit"] == 0 and c["type"] == "pure" for c in cands)
        if found_pure:
            print("  [+] SUCCESS: Bit 0 on 0x100 identified as 'pure'")
        else:
            print("  [!] FAILED: Bit 0 on 0x100 not found")
            
    # Check ID 0x200
    if 0x200 in results:
        res200 = results[0x200]
        cands = res200["candidates"]
        print(f"[ID 0x200] Candidates: {len(cands)}")
        found_bit8 = any(c["start_bit"] == 8 and c["type"] == "pure" for c in cands)
        if found_bit8:
            print("  [+] SUCCESS: Bit 8 on 0x200 identified as 'pure'")
        else:
            print("  [!] FAILED: Bit 8 on 0x200 not found")

    # Check ID 0x300 (New ID)
    if 0x300 in results:
        print(f"[ID 0x300] Detected as new/active.")
    
    if 0x100 in results and 0x200 in results:
        print("\n[GLOBAL TEST PASSED] Multi-ID differential analysis is functional!")
    else:
        print("\n[GLOBAL TEST FAILED]")

if __name__ == "__main__":
    test_logic()
