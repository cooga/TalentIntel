#!/usr/bin/env python3
"""
通过CDP+JS提取LinkedIn档案信息 - 已验证可用
"""
import json, time, random, os, sys
from datetime import datetime
from playwright.sync_api import sync_playwright

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/Project/TalentIntel/data")
DB_FILE = os.path.join(DATA_DIR, "clean_candidates_db.json")
CDP_URL = "http://127.0.0.1:18800"

EXTRACT_JS = """() => {
  const result = {};
  const sections = document.querySelectorAll('section');
  sections.forEach((sec, i) => {
    const h2 = sec.querySelector('h2');
    if (!h2) return;
    const title = h2.innerText.trim().toLowerCase();
    const text = sec.innerText.trim();
    if (title === 'about') result.about = text.replace(/^About\\n?/, '').substring(0, 800);
    if (title === 'experience') result.experience = text.replace(/^Experience\\n?/, '').substring(0, 3000);
    if (title === 'education') result.education = text.replace(/^Education\\n?/, '').substring(0, 800);
    if (title === 'skills') result.skills = text.replace(/^Skills\\n?/, '').substring(0, 500);
    if (title === 'publications') result.publications = text.replace(/^Publications\\n?/, '').substring(0, 800);
    if (title === 'patents') result.patents = text.replace(/^Patents\\n?/, '').substring(0, 500);
    if (title === 'honors & awards') result.honors = text.replace(/^Honors & awards\\n?/, '').substring(0, 500);
    if (i === 1) result.headline = text.substring(0, 300);
  });
  return JSON.stringify(result);
}"""

def build_recommendation(c, info):
    """基于LinkedIn详细信息生成推荐理由"""
    parts = []
    
    # 1. 工作履历
    if info.get("experience"):
        exp = info["experience"]
        # 提取公司和职位
        lines = [l.strip() for l in exp.split('\n') if l.strip()]
        exp_items = []
        i = 0
        while i < len(lines) and len(exp_items) < 5:
            line = lines[i]
            # 跳过常见噪音
            if any(skip in line.lower() for skip in ['show all', 'endorsement', '·']):
                i += 1
                continue
            # 检测是否是职位行（通常较短且不含特殊字符）
            if len(line) < 80 and not line.startswith('•') and not line.startswith('-'):
                exp_items.append(line)
            i += 1
        if exp_items:
            parts.append(f"【工作履历】{'; '.join(exp_items[:5])}")
    
    if not parts or "工作履历" not in parts[0]:
        parts.insert(0, f"【工作履历】现任 {c.get('title','')} @ {c.get('company','')}")
    
    # 2. 教育背景
    if info.get("education"):
        edu = info["education"].replace("Show all", "").strip()
        parts.append(f"【教育背景】{edu[:300]}")
    
    # 3. 个人简介/研究方向
    if info.get("about"):
        about = info["about"].replace("Skills", "").strip()
        parts.append(f"【研究方向】{about[:300]}")
    
    # 4. 技能
    if info.get("skills"):
        skills = info["skills"].replace("Show all", "").strip()
        # 清理endorsement信息
        skill_lines = [l.strip() for l in skills.split('\n') if l.strip() and 'endors' not in l.lower() and 'colleague' not in l.lower() and len(l.strip()) < 50]
        if skill_lines:
            parts.append(f"【技能专长】{', '.join(skill_lines[:8])}")
    
    # 5. 学术成果
    if info.get("publications"):
        pubs = info["publications"].replace("Show publication", "").strip()
        pub_lines = [l.strip() for l in pubs.split('\n') if l.strip() and len(l.strip()) > 10]
        if pub_lines:
            parts.append(f"【学术论文】{'; '.join(pub_lines[:3])}")
    
    # 6. 专利
    if info.get("patents"):
        patents = info["patents"].replace("Show patent", "").strip()
        pat_lines = [l.strip() for l in patents.split('\n') if l.strip() and len(l.strip()) > 10 and 'inventor' not in l.lower()]
        if pat_lines:
            parts.append(f"【专利】{'; '.join(pat_lines[:2])}")
    
    # 7. 荣誉
    if info.get("honors"):
        honors = info["honors"].replace("Show all", "").strip()
        hon_lines = [l.strip() for l in honors.split('\n') if l.strip() and len(l.strip()) > 10]
        if hon_lines:
            parts.append(f"【荣誉奖项】{'; '.join(hon_lines[:2])}")
    
    return " | ".join(parts)


def main():
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    
    candidates = data.get('candidates', [])
    verified = [(i, c) for i, c in enumerate(candidates) 
                if c.get('verification_status') == 'verified' and c.get('linkedin_url')]
    verified.sort(key=lambda x: x[1].get('match_score', 0), reverse=True)
    
    print(f"开始抓取 {len(verified)} 位候选人的LinkedIn详细信息...")
    sys.stdout.flush()
    
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = context.new_page()
        
        success = 0
        failed = 0
        
        for count, (idx, c) in enumerate(verified):
            name = c.get('name', 'N/A')
            url = c.get('linkedin_url', '')
            
            print(f"  [{count+1}/{len(verified)}] {name}...", end=" ", flush=True)
            
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                time.sleep(random.uniform(2, 4))
                
                # 滚动加载
                for _ in range(5):
                    page.evaluate("window.scrollBy(0, 600)")
                    time.sleep(random.uniform(0.5, 1.0))
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(1)
                
                # JS提取
                raw = page.evaluate(EXTRACT_JS)
                info = json.loads(raw)
                
                has = lambda k: "✓" if info.get(k) else "✗"
                print(f"教育:{has('education')} 经历:{has('experience')} 简介:{has('about')} 技能:{has('skills')}", end="")
                
                # 生成推荐理由
                new_bg = build_recommendation(c, info)
                if new_bg:
                    candidates[idx]['background'] = new_bg
                
                # 保存原始数据
                if info.get("education"):
                    candidates[idx]['education_raw'] = info['education']
                if info.get("experience"):
                    candidates[idx]['experience_raw'] = info['experience']
                if info.get("about"):
                    candidates[idx]['about'] = info['about']
                if info.get("skills"):
                    candidates[idx]['skills_raw'] = info['skills']
                if info.get("publications"):
                    candidates[idx]['publications_raw'] = info['publications']
                if info.get("headline"):
                    candidates[idx]['headline'] = info['headline']
                if info.get("patents"):
                    candidates[idx]['patents_raw'] = info['patents']
                if info.get("honors"):
                    candidates[idx]['honors_raw'] = info['honors']
                candidates[idx]['enriched'] = True
                candidates[idx]['enriched_at'] = datetime.now().isoformat()
                
                print(f" ✅")
                success += 1
                
            except Exception as e:
                print(f" ❌ {str(e)[:50]}")
                failed += 1
            
            # 每10个保存一次
            if (count + 1) % 10 == 0:
                with open(DB_FILE, 'w') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"  💾 已保存 ({count+1}/{len(verified)})")
                sys.stdout.flush()
            
            time.sleep(random.uniform(4, 8))
        
        page.close()
    
    # 最终保存
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*50}")
    print(f"✅ 完成! 成功: {success}, 失败: {failed}")
    print(f"数据库已保存: {DB_FILE}")


if __name__ == "__main__":
    main()
