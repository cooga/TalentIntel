#!/usr/bin/env python3
"""
通过CDP连接已登录LinkedIn的Chrome浏览器，批量抓取候选人详细信息
"""
import json, time, random, os, re, sys
from datetime import datetime
from playwright.sync_api import sync_playwright

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/Project/TalentIntel/data")
DB_FILE = os.path.join(DATA_DIR, "clean_candidates_db.json")
CDP_URL = "http://127.0.0.1:18800"

def extract_profile(page, url, name):
    """访问LinkedIn页面并提取详细信息"""
    result = {"education": [], "experience": [], "skills": [], "about": "", "headline": ""}
    
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        time.sleep(random.uniform(3, 5))
        
        # 滚动加载更多内容
        for _ in range(4):
            page.evaluate("window.scrollBy(0, 600)")
            time.sleep(random.uniform(0.8, 1.5))
        
        # 回到顶部
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)
        
        body = page.inner_text("body")
        
        # 提取headline
        try:
            hl = page.query_selector("div.text-body-medium")
            if hl:
                result["headline"] = hl.inner_text().strip()[:200]
        except:
            pass
        
        # 提取About
        try:
            about_sections = page.query_selector_all("section")
            for sec in about_sections:
                try:
                    h2 = sec.query_selector("h2, [id*='about']")
                    if h2 and "about" in h2.inner_text().lower():
                        spans = sec.query_selector_all("span[aria-hidden='true']")
                        for sp in spans:
                            txt = sp.inner_text().strip()
                            if len(txt) > 50:
                                result["about"] = txt[:500]
                                break
                        break
                except:
                    continue
        except:
            pass
        
        # 提取Experience
        try:
            exp_items = []
            sections = page.query_selector_all("section")
            for sec in sections:
                try:
                    h2 = sec.query_selector("h2")
                    if h2 and "experience" in h2.inner_text().lower():
                        items = sec.query_selector_all("li")
                        for item in items[:8]:
                            spans = item.query_selector_all("span[aria-hidden='true']")
                            texts = [s.inner_text().strip() for s in spans if s.inner_text().strip()]
                            if texts:
                                exp_items.append(" | ".join(texts[:4]))
                        break
                except:
                    continue
            result["experience"] = exp_items[:8]
        except:
            pass
        
        # 提取Education
        try:
            sections = page.query_selector_all("section")
            for sec in sections:
                try:
                    h2 = sec.query_selector("h2")
                    if h2 and "education" in h2.inner_text().lower():
                        items = sec.query_selector_all("li")
                        for item in items[:5]:
                            spans = item.query_selector_all("span[aria-hidden='true']")
                            texts = [s.inner_text().strip() for s in spans if s.inner_text().strip()]
                            if texts:
                                result["education"].append(" | ".join(texts[:4]))
                        break
                except:
                    continue
        except:
            pass
        
        # 提取Skills
        try:
            sections = page.query_selector_all("section")
            for sec in sections:
                try:
                    h2 = sec.query_selector("h2")
                    if h2 and "skill" in h2.inner_text().lower():
                        items = sec.query_selector_all("span[aria-hidden='true']")
                        for item in items[:12]:
                            txt = item.inner_text().strip()
                            if txt and len(txt) < 50 and txt not in ["Show all skills", "Endorsements"]:
                                result["skills"].append(txt)
                        result["skills"] = list(dict.fromkeys(result["skills"]))[:10]
                        break
                except:
                    continue
        except:
            pass
        
    except Exception as e:
        result["error"] = str(e)[:100]
    
    return result


def build_recommendation(c, info):
    """基于抓取信息生成详细推荐理由"""
    parts = []
    
    # 工作履历
    if info.get("experience"):
        exp_str = "; ".join(info["experience"][:4])
        parts.append(f"【工作履历】{exp_str}")
    else:
        parts.append(f"【工作履历】现任 {c.get('title','')} @ {c.get('company','')}")
    
    # 教育背景
    if info.get("education"):
        edu_str = "; ".join(info["education"][:3])
        parts.append(f"【教育背景】{edu_str}")
    
    # 个人简介
    if info.get("about"):
        parts.append(f"【个人简介】{info['about'][:200]}")
    
    # 技能专长
    if info.get("skills"):
        parts.append(f"【技能专长】{', '.join(info['skills'][:8])}")
    
    # Headline
    if info.get("headline"):
        parts.append(f"【职位描述】{info['headline']}")
    
    return " | ".join(parts) if parts else c.get("background", "")


def main():
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    
    candidates = data.get('candidates', [])
    verified = [(i, c) for i, c in enumerate(candidates) if c.get('verification_status') == 'verified' and c.get('linkedin_url')]
    verified.sort(key=lambda x: x[1].get('match_score', 0), reverse=True)
    
    print(f"LinkedIn已登录，开始抓取 {len(verified)} 位候选人...")
    print(f"CDP: {CDP_URL}")
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
            
            info = extract_profile(page, url, name)
            
            if info.get("error"):
                print(f"❌ {info['error'][:40]}")
                failed += 1
            else:
                has_edu = "✓" if info.get("education") else "✗"
                has_exp = "✓" if info.get("experience") else "✗"
                has_about = "✓" if info.get("about") else "✗"
                has_skills = "✓" if info.get("skills") else "✗"
                
                # 更新推荐理由
                new_bg = build_recommendation(c, info)
                if new_bg and len(new_bg) > len(c.get('background', '')):
                    candidates[idx]['background'] = new_bg
                
                # 保存详细字段
                if info.get("education"):
                    candidates[idx]['education'] = info['education']
                if info.get("experience"):
                    candidates[idx]['experience_history'] = info['experience']
                if info.get("skills"):
                    candidates[idx]['skills_list'] = info['skills']
                if info.get("about"):
                    candidates[idx]['about'] = info['about']
                if info.get("headline"):
                    candidates[idx]['headline'] = info['headline']
                candidates[idx]['enriched'] = True
                candidates[idx]['enriched_at'] = datetime.now().isoformat()
                
                print(f"教育:{has_edu} 经历:{has_exp} 简介:{has_about} 技能:{has_skills}")
                success += 1
            
            # 每10个保存一次
            if (count + 1) % 10 == 0:
                with open(DB_FILE, 'w') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"  💾 已保存 ({count+1}/{len(verified)})")
            
            delay = random.uniform(5, 10)
            time.sleep(delay)
        
        page.close()
    
    # 最终保存
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*50}")
    print(f"✅ 完成! 成功: {success}, 失败: {failed}")
    print(f"数据库已保存: {DB_FILE}")


if __name__ == "__main__":
    main()
