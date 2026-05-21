#!/usr/bin/env python3
"""
LinkedIn详细档案批量抓取脚本
- 使用Playwright访问已验证候选人的LinkedIn页面
- 提取教育背景、工作经历、技能等信息
- 更新clean_candidates_db.json
"""

import json
import time
import random
import os
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/Project/TalentIntel/data")
DB_FILE = os.path.join(DATA_DIR, "clean_candidates_db.json")
PROFILE_DIR = os.path.join(DATA_DIR, "profiles/linkedin_01")
OUTPUT_FILE = os.path.join(DATA_DIR, "enriched_candidates.json")
LOG_FILE = os.path.join(DATA_DIR, "enrichment_log.json")

def extract_profile_info(page, url):
    """从LinkedIn页面提取详细信息"""
    result = {
        "about": "",
        "experience": [],
        "education": [],
        "skills": [],
        "publications": [],
        "raw_text": ""
    }
    
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(random.uniform(3, 6))
        
        # 滚动页面加载更多内容
        for _ in range(3):
            page.evaluate("window.scrollBy(0, 800)")
            time.sleep(random.uniform(1, 2))
        
        # 获取页面全文
        body_text = page.inner_text("body")
        result["raw_text"] = body_text[:5000]
        
        # 提取About部分
        try:
            about_section = page.query_selector('section.summary, div[class*="about"], #about')
            if about_section:
                result["about"] = about_section.inner_text()[:500]
        except:
            pass
        
        # 尝试从全文中提取About
        if not result["about"]:
            about_match = re.search(r'About\n(.+?)(?:\nActivity|\nExperience|\nEducation)', body_text, re.DOTALL)
            if about_match:
                result["about"] = about_match.group(1).strip()[:500]
        
        # 提取Experience部分
        exp_match = re.search(r'Experience\n(.+?)(?:\nEducation|\nSkills|\nPublications|\nLanguages)', body_text, re.DOTALL)
        if exp_match:
            exp_text = exp_match.group(1).strip()
            # 解析经历条目
            lines = [l.strip() for l in exp_text.split('\n') if l.strip()]
            result["experience"] = lines[:20]  # 最多20行
        
        # 提取Education部分
        edu_match = re.search(r'Education\n(.+?)(?:\nSkills|\nPublications|\nLanguages|\nOther)', body_text, re.DOTALL)
        if edu_match:
            edu_text = edu_match.group(1).strip()
            lines = [l.strip() for l in edu_text.split('\n') if l.strip()]
            result["education"] = lines[:10]
        
        # 提取Skills部分
        skills_match = re.search(r'Skills\n(.+?)(?:\nPublications|\nLanguages|\nOther|\nRecommendations)', body_text, re.DOTALL)
        if skills_match:
            skills_text = skills_match.group(1).strip()
            lines = [l.strip() for l in skills_text.split('\n') if l.strip() and len(l.strip()) < 50]
            result["skills"] = lines[:15]
        
        # 提取Publications部分
        pub_match = re.search(r'Publications\n(.+?)(?:\nLanguages|\nOther|\nRecommendations|\nCourses)', body_text, re.DOTALL)
        if pub_match:
            pub_text = pub_match.group(1).strip()
            lines = [l.strip() for l in pub_text.split('\n') if l.strip()]
            result["publications"] = lines[:10]
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def generate_detailed_recommendation(candidate, profile_info):
    """基于抓取的详细信息生成推荐理由"""
    
    name = candidate.get('name', '')
    title = candidate.get('title', '')
    company = candidate.get('company', '')
    location = candidate.get('location', '')
    
    about = profile_info.get('about', '')
    experience = profile_info.get('experience', [])
    education = profile_info.get('education', [])
    skills = profile_info.get('skills', [])
    publications = profile_info.get('publications', [])
    
    sections = []
    
    # 1. 工作履历
    if experience:
        exp_summary = '; '.join(experience[:5])
        sections.append(f"【工作履历】{exp_summary}")
    else:
        sections.append(f"【工作履历】现任 {title} @ {company}")
    
    # 2. 教育背景
    if education:
        edu_summary = '; '.join(education[:3])
        sections.append(f"【教育背景】{edu_summary}")
    else:
        # 从about或title推断
        title_lower = title.lower()
        if 'phd' in title_lower or 'ph.d' in title_lower:
            sections.append("【教育背景】博士学位")
        elif 'postdoc' in title_lower:
            sections.append("【教育背景】博士后研究经历")
        elif 'professor' in title_lower:
            sections.append("【教育背景】教授/教职背景（推断博士学位）")
    
    # 3. 学术成果
    if publications:
        pub_summary = '; '.join(publications[:3])
        sections.append(f"【学术成果】{pub_summary}")
    
    # 4. 技能专长
    if skills:
        skills_summary = ', '.join(skills[:8])
        sections.append(f"【技能专长】{skills_summary}")
    else:
        # 从title推断
        title_lower = title.lower()
        skill_tags = []
        if any(kw in title_lower for kw in ['ai', 'ml', 'machine learning', 'deep learning']):
            skill_tags.append("AI/ML")
        if any(kw in title_lower for kw in ['wireless', '5g', '6g', 'ran', 'communication']):
            skill_tags.append("无线通信")
        if skill_tags:
            sections.append(f"【技能专长】{', '.join(skill_tags)}")
    
    # 5. 工业/学术分类
    company_lower = company.lower()
    top_companies = {
        'nvidia': 'AI芯片/计算领军', 'qualcomm': '无线通信巨头',
        'apple': '消费电子顶尖', 'google': 'AI/搜索巨头',
        'intel': 'CPU/芯片巨头', 'amd': 'GPU/CPU芯片',
        'broadcom': '通信芯片巨头', 'marvell': '存储/网络芯片',
        'samsung': '电子制造巨头', 'spacex': '航天工程顶尖'
    }
    
    for comp_key, comp_desc in top_companies.items():
        if comp_key in company_lower:
            sections.append(f"【公司定位】{comp_desc}")
            break
    
    # 6. 地理位置
    loc_lower = location.lower()
    if any(x in loc_lower for x in ['california', 'ca', 'san jose', 'santa clara', 'cupertino', 'san diego']):
        sections.append("【地理位置】加州科技中心")
    elif any(x in loc_lower for x in ['texas', 'austin']):
        sections.append("【地理位置】德州科技中心")
    elif 'united states' in loc_lower:
        sections.append("【地理位置】美国本土")
    elif 'canada' in loc_lower:
        sections.append("【地理位置】加拿大")
    elif any(x in loc_lower for x in ['uk', 'cambridge']):
        sections.append("【地理位置】英国")
    
    return " | ".join(sections)


def main():
    # 加载候选人数据
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    
    candidates = data.get('candidates', [])
    verified = [c for c in candidates if c.get('verification_status') == 'verified']
    verified_sorted = sorted(verified, key=lambda x: x.get('match_score', 0), reverse=True)
    
    print(f"开始抓取 {len(verified_sorted)} 位验证过候选人的LinkedIn详细信息...")
    print(f"预计耗时: {len(verified_sorted) * 15 / 60:.0f} 分钟")
    
    enrichment_log = {
        "start_time": datetime.now().isoformat(),
        "total": len(verified_sorted),
        "success": 0,
        "failed": 0,
        "results": []
    }
    
    with sync_playwright() as p:
        # 启动浏览器（使用已有Profile）
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        # 使用已有Profile的上下文
        if os.path.exists(PROFILE_DIR):
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
        else:
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
        
        page = context.new_page()
        
        for idx, candidate in enumerate(verified_sorted):
            name = candidate.get('name', 'N/A')
            linkedin_url = candidate.get('linkedin_url', '')
            
            if not linkedin_url:
                print(f"  [{idx+1}/{len(verified_sorted)}] {name} - 无LinkedIn链接，跳过")
                enrichment_log["results"].append({
                    "name": name,
                    "status": "skipped",
                    "reason": "no_linkedin_url"
                })
                continue
            
            print(f"  [{idx+1}/{len(verified_sorted)}] {name} - 正在抓取...")
            
            try:
                profile_info = extract_profile_info(page, linkedin_url)
                
                if profile_info.get("error"):
                    print(f"    ❌ 错误: {profile_info['error'][:50]}")
                    enrichment_log["results"].append({
                        "name": name,
                        "status": "error",
                        "error": profile_info["error"][:100]
                    })
                    enrichment_log["failed"] += 1
                else:
                    # 生成新的推荐理由
                    new_recommendation = generate_detailed_recommendation(candidate, profile_info)
                    
                    # 更新候选人数据
                    for c in candidates:
                        if c.get('linkedin_url') == linkedin_url:
                            c['background'] = new_recommendation
                            c['enriched'] = True
                            c['enriched_at'] = datetime.now().isoformat()
                            if profile_info.get('education'):
                                c['education'] = profile_info['education']
                            if profile_info.get('experience'):
                                c['experience_history'] = profile_info['experience']
                            if profile_info.get('skills'):
                                c['skills_list'] = profile_info['skills']
                            if profile_info.get('about'):
                                c['about'] = profile_info['about']
                            if profile_info.get('publications'):
                                c['publications'] = profile_info['publications']
                            break
                    
                    has_edu = "✓" if profile_info.get('education') else "✗"
                    has_exp = "✓" if profile_info.get('experience') else "✗"
                    has_skills = "✓" if profile_info.get('skills') else "✗"
                    print(f"    ✅ 完成 (教育:{has_edu} 经历:{has_exp} 技能:{has_skills})")
                    
                    enrichment_log["results"].append({
                        "name": name,
                        "status": "success",
                        "has_education": bool(profile_info.get('education')),
                        "has_experience": bool(profile_info.get('experience')),
                        "has_skills": bool(profile_info.get('skills')),
                        "has_publications": bool(profile_info.get('publications'))
                    })
                    enrichment_log["success"] += 1
                
            except Exception as e:
                print(f"    ❌ 异常: {str(e)[:50]}")
                enrichment_log["results"].append({
                    "name": name,
                    "status": "exception",
                    "error": str(e)[:100]
                })
                enrichment_log["failed"] += 1
            
            # 随机延迟（8-15秒）
            delay = random.uniform(8, 15)
            print(f"    等待 {delay:.1f}s...")
            time.sleep(delay)
        
        browser.close()
    
    # 保存更新后的数据库
    enrichment_log["end_time"] = datetime.now().isoformat()
    
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    with open(LOG_FILE, 'w') as f:
        json.dump(enrichment_log, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*50}")
    print(f"抓取完成!")
    print(f"  成功: {enrichment_log['success']}")
    print(f"  失败: {enrichment_log['failed']}")
    print(f"  数据库已更新: {DB_FILE}")
    print(f"  日志已保存: {LOG_FILE}")


if __name__ == "__main__":
    main()
