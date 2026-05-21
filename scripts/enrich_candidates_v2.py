#!/usr/bin/env python3
"""
轻量级LinkedIn档案信息抓取 + 深度推断
- 用requests抓取LinkedIn公开页面
- 结合email域名推断教育背景
- 基于职位/公司深度分析
"""

import json
import time
import random
import os
import re
import requests
from datetime import datetime
from html import unescape

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/Project/TalentIntel/data")
DB_FILE = os.path.join(DATA_DIR, "clean_candidates_db.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9"
}

# 大学域名映射
UNIVERSITY_DOMAINS = {
    'rice.edu': 'Rice University',
    'stanford.edu': 'Stanford University',
    'mit.edu': 'MIT',
    'berkeley.edu': 'UC Berkeley',
    'cmu.edu': 'Carnegie Mellon University',
    'gatech.edu': 'Georgia Tech',
    'utexas.edu': 'UT Austin',
    'umich.edu': 'University of Michigan',
    'uiuc.edu': 'UIUC',
    'cornell.edu': 'Cornell University',
    'princeton.edu': 'Princeton University',
    'columbia.edu': 'Columbia University',
    'ucla.edu': 'UCLA',
    'ucsd.edu': 'UC San Diego',
    'usc.edu': 'USC',
    'purdue.edu': 'Purdue University',
    'buffalo.edu': 'University at Buffalo',
    'virginia.edu': 'University of Virginia',
    'vt.edu': 'Virginia Tech',
    'cam.ac.uk': 'University of Cambridge',
    'ox.ac.uk': 'University of Oxford',
    'leeds.ac.uk': 'University of Leeds',
    'nus.edu.sg': 'NUS Singapore',
    'ntu.edu.sg': 'NTU Singapore',
    'tsinghua.edu.cn': 'Tsinghua University',
    'pku.edu.cn': 'Peking University',
    'zju.edu.cn': 'Zhejiang University',
    'ustc.edu.cn': 'USTC',
    'sjtu.edu.cn': 'Shanghai Jiao Tong University',
    'hku.hk': 'University of Hong Kong',
    'cuhk.edu.hk': 'CUHK'
}

# 公司背景知识库
COMPANY_KNOWLEDGE = {
    'nvidia': {
        'industry': 'AI芯片/GPU计算',
        'focus': 'AI加速计算、GPU架构、自动驾驶、AI-RAN',
        'tier': 'Tier 1',
        'hq': '圣克拉拉'
    },
    'qualcomm': {
        'industry': '无线通信芯片',
        'focus': '5G/6G基带、AI推理、Wi-Fi、蓝牙',
        'tier': 'Tier 1',
        'hq': '圣地亚哥'
    },
    'apple': {
        'industry': '消费电子/芯片设计',
        'focus': 'AI/ML、芯片设计、无线技术、操作系统',
        'tier': 'Tier 1',
        'hq': '库比蒂诺'
    },
    'intel': {
        'industry': 'CPU/半导体',
        'focus': 'CPU架构、AI加速、5G基站、FPGA',
        'tier': 'Tier 1',
        'hq': '圣克拉拉'
    },
    'amd': {
        'industry': 'GPU/CPU芯片',
        'focus': 'GPU计算、AI推理、高性能计算',
        'tier': 'Tier 1',
        'hq': '圣克拉拉'
    },
    'broadcom': {
        'industry': '通信芯片',
        'focus': '网络芯片、存储、光通信、Wi-Fi',
        'tier': 'Tier 1',
        'hq': '圣何塞'
    },
    'marvell': {
        'industry': '存储/网络芯片',
        'focus': '数据基础设施、5G基站芯片、存储控制器',
        'tier': 'Tier 1',
        'hq': '威尔明顿'
    },
    'samsung': {
        'industry': '电子制造/半导体',
        'focus': '5G/6G、AI、芯片制造、消费电子',
        'tier': 'Tier 1',
        'hq': '首尔'
    },
    'spacex': {
        'industry': '航天工程',
        'focus': 'Starlink卫星通信、火箭发射',
        'tier': 'Tier 1',
        'hq': '霍桑'
    },
    'nokia': {
        'industry': '通信设备',
        'focus': '5G基站、Bell Labs研究、网络设备',
        'tier': 'Tier 1',
        'hq': '赫尔辛基'
    },
    'google': {
        'industry': '互联网/AI',
        'focus': 'AI/ML、搜索、云计算、Android',
        'tier': 'Tier 1',
        'hq': '山景城'
    }
}

# 职位级别知识库
LEVEL_KNOWLEDGE = {
    'intern': {'level': '实习', 'years': '0', 'seniority': 1},
    'engineer': {'level': '工程师', 'years': '2-5', 'seniority': 3},
    'senior': {'level': '高级工程师', 'years': '5-8', 'seniority': 5},
    'staff': {'level': 'Staff工程师', 'years': '8-12', 'seniority': 7},
    'principal': {'level': 'Principal工程师', 'years': '12-15', 'seniority': 8},
    'director': {'level': '总监', 'years': '10-15', 'seniority': 9},
    'vp': {'level': '副总裁', 'years': '15+', 'seniority': 10},
    'fellow': {'level': 'Fellow', 'years': '15+', 'seniority': 10},
    'researcher': {'level': '研究员', 'years': '3-8', 'seniority': 5},
    'research scientist': {'level': '研究科学家', 'years': '5-10', 'seniority': 6},
    'postdoc': {'level': '博士后', 'years': '0-3', 'seniority': 4},
    'professor': {'level': '教授', 'years': '10+', 'seniority': 8},
    'assistant professor': {'level': '助理教授', 'years': '3-7', 'seniority': 6},
    'associate professor': {'level': '副教授', 'years': '7-12', 'seniority': 7}
}


def fetch_linkedin_public(url):
    """尝试抓取LinkedIn公开页面信息"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        if resp.status_code == 200:
            text = resp.text
            
            result = {}
            
            # 提取About
            about_match = re.search(r'"summary":"([^"]*)"', text)
            if about_match:
                result['about'] = unescape(about_match.group(1))[:500]
            
            # 提取headline
            headline_match = re.search(r'"headline":"([^"]*)"', text)
            if headline_match:
                result['headline'] = unescape(headline_match.group(1))
            
            # 提取学校信息
            edu_matches = re.findall(r'"schoolName":"([^"]*)"', text)
            if edu_matches:
                result['schools'] = list(set(edu_matches))
            
            # 提取公司信息
            comp_matches = re.findall(r'"companyName":"([^"]*)"', text)
            if comp_matches:
                result['companies'] = list(set(comp_matches))
            
            # 提取技能
            skill_matches = re.findall(r'"skillName":"([^"]*)"', text)
            if skill_matches:
                result['skills'] = list(set(skill_matches))[:15]
            
            # 提取学位
            degree_matches = re.findall(r'"degreeName":"([^"]*)"', text)
            if degree_matches:
                result['degrees'] = list(set(degree_matches))
            
            # 提取专业
            fos_matches = re.findall(r'"fieldOfStudy":"([^"]*)"', text)
            if fos_matches:
                result['fields_of_study'] = list(set(fos_matches))
            
            return result
        return {}
    except:
        return {}


def infer_education_from_email(email):
    """从email域名推断教育背景"""
    if not email:
        return None
    domain = email.split('@')[-1] if '@' in email else ''
    for uni_domain, uni_name in UNIVERSITY_DOMAINS.items():
        if uni_domain in domain:
            return uni_name
    return None


def get_level_info(title):
    """获取职位级别信息"""
    title_lower = title.lower()
    for key, info in sorted(LEVEL_KNOWLEDGE.items(), key=lambda x: -len(x[0])):
        if key in title_lower:
            return info
    return {'level': '未知级别', 'years': '未知', 'seniority': 3}


def get_company_info(company):
    """获取公司背景信息"""
    company_lower = company.lower()
    for key, info in COMPANY_KNOWLEDGE.items():
        if key in company_lower:
            return info
    return None


def compute_match_score(candidate, linkedin_info):
    """基于丰富后的信息重新计算匹配度"""
    title = candidate.get('title', '').lower()
    company = candidate.get('company', '').lower()
    
    # AI维度
    ai_keywords = ['ai', 'machine learning', 'deep learning', 'ml', 'neural', 'llm', 
                   'foundation model', 'data scientist', 'computer vision']
    ai_score = min(1.0, sum(0.25 for kw in ai_keywords if kw in title) + 
                   sum(0.15 for kw in ai_keywords if kw in str(linkedin_info.get('about', '')).lower()) +
                   sum(0.1 for skill in linkedin_info.get('skills', []) if any(kw in skill.lower() for kw in ai_keywords)))
    
    # Wireless维度
    wireless_keywords = ['wireless', '5g', '6g', 'ran', 'communication', 'signal processing',
                        'modem', 'baseband', 'rf', 'mimo', 'ofdm', 'cellular']
    wireless_score = min(1.0, sum(0.25 for kw in wireless_keywords if kw in title) +
                        sum(0.15 for kw in wireless_keywords if kw in str(linkedin_info.get('about', '')).lower()) +
                        sum(0.1 for skill in linkedin_info.get('skills', []) if any(kw in skill.lower() for kw in wireless_keywords)))
    
    # 级别
    level_info = get_level_info(candidate.get('title', ''))
    level_score = level_info['seniority'] / 10.0
    
    # 公司
    company_info = get_company_info(candidate.get('company', ''))
    company_score = 0.9 if company_info else 0.5
    
    # 教育
    edu_score = 0.5
    schools = linkedin_info.get('schools', [])
    degrees = linkedin_info.get('degrees', [])
    if any('phd' in d.lower() or 'doctor' in d.lower() for d in degrees):
        edu_score = 0.9
    elif any('master' in d.lower() for d in degrees):
        edu_score = 0.7
    
    # 交叉奖励
    cross_bonus = 0.15 if (ai_score > 0 and wireless_score > 0) else 0
    
    # 综合 (AI 25% + Wireless 25% + Level 15% + Company 15% + Education 10% + Cross 10%)
    final = (ai_score * 0.25 + wireless_score * 0.25 + level_score * 0.15 + 
             company_score * 0.15 + edu_score * 0.10 + cross_bonus)
    
    return round(min(1.0, final), 2)


def generate_recommendation(candidate, linkedin_info):
    """生成详细推荐理由"""
    name = candidate.get('name', '')
    title = candidate.get('title', '')
    company = candidate.get('company', '')
    location = candidate.get('location', '')
    email = candidate.get('email', '')
    
    sections = []
    
    # 1. 工作履历
    companies = linkedin_info.get('companies', [])
    if companies:
        companies_str = ' → '.join(companies[:5])
        sections.append(f"【工作履历】{companies_str}")
    else:
        sections.append(f"【工作履历】现任 {title} @ {company}")
    
    # 2. 教育背景
    schools = linkedin_info.get('schools', [])
    degrees = linkedin_info.get('degrees', [])
    fields = linkedin_info.get('fields_of_study', [])
    
    edu_parts = []
    if schools:
        for i, school in enumerate(schools[:3]):
            degree = degrees[i] if i < len(degrees) else ''
            field = fields[i] if i < len(fields) else ''
            parts = [p for p in [degree, field, school] if p]
            edu_parts.append(', '.join(parts))
    
    # 从email推断
    email_uni = infer_education_from_email(email)
    if email_uni and email_uni not in str(schools):
        edu_parts.append(f"{email_uni} (邮箱推断)")
    
    if edu_parts:
        sections.append(f"【教育背景】{'; '.join(edu_parts)}")
    else:
        title_lower = title.lower()
        if 'phd' in title_lower or 'ph.d' in title_lower:
            sections.append("【教育背景】博士学位")
        elif 'postdoc' in title_lower:
            sections.append("【教育背景】博士后研究经历")
        elif 'professor' in title_lower:
            sections.append("【教育背景】教授（推断博士学位）")
    
    # 3. 技能专长
    skills = linkedin_info.get('skills', [])
    about = linkedin_info.get('about', '')
    
    if skills:
        sections.append(f"【技能专长】{', '.join(skills[:8])}")
    else:
        title_lower = title.lower()
        skill_tags = []
        if any(kw in title_lower for kw in ['ai', 'ml', 'machine learning', 'deep learning']):
            skill_tags.append("AI/ML")
        if any(kw in title_lower for kw in ['wireless', '5g', '6g', 'ran', 'communication']):
            skill_tags.append("无线通信/5G/6G")
        if any(kw in title_lower for kw in ['signal processing']):
            skill_tags.append("信号处理")
        if any(kw in title_lower for kw in ['system']):
            skill_tags.append("系统设计")
        if skill_tags:
            sections.append(f"【技能专长】{', '.join(skill_tags)}")
    
    # 4. About摘要
    if about:
        sections.append(f"【个人简介】{about[:200]}")
    
    # 5. 工业/学术定位
    company_info = get_company_info(company)
    if company_info:
        sections.append(f"【公司定位】{company_info['industry']} ({company_info['tier']}) - {company_info['focus']}")
    
    # 6. 职位级别
    level_info = get_level_info(title)
    sections.append(f"【职位级别】{level_info['level']}（预估经验 {level_info['years']}年）")
    
    # 7. 地理位置
    loc_lower = location.lower()
    if 'san diego' in loc_lower:
        sections.append("【地理位置】圣地亚哥（Qualcomm总部所在地）")
    elif any(x in loc_lower for x in ['san jose', 'santa clara', 'cupertino', 'sunnyvale', 'palo alto']):
        sections.append("【地理位置】硅谷核心区")
    elif 'austin' in loc_lower:
        sections.append("【地理位置】奥斯汀科技中心")
    elif 'california' in loc_lower:
        sections.append("【地理位置】加州")
    elif 'texas' in loc_lower:
        sections.append("【地理位置】德州")
    elif 'united states' in loc_lower:
        sections.append("【地理位置】美国")
    elif 'canada' in loc_lower:
        sections.append("【地理位置】加拿大")
    elif any(x in loc_lower for x in ['uk', 'cambridge', 'london']):
        sections.append("【地理位置】英国")
    elif 'hong kong' in loc_lower:
        sections.append("【地理位置】香港")
    
    return " | ".join(sections)


def main():
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    
    candidates = data.get('candidates', [])
    verified = [i for i, c in enumerate(candidates) if c.get('verification_status') == 'verified']
    
    print(f"开始丰富 {len(verified)} 位验证过候选人的信息...")
    
    success = 0
    linkedin_enriched = 0
    
    for count, idx in enumerate(verified):
        c = candidates[idx]
        name = c.get('name', 'N/A')
        linkedin_url = c.get('linkedin_url', '')
        
        print(f"  [{count+1}/{len(verified)}] {name}...", end=" ", flush=True)
        
        # 尝试抓取LinkedIn公开信息
        linkedin_info = {}
        if linkedin_url:
            linkedin_info = fetch_linkedin_public(linkedin_url)
            if linkedin_info:
                linkedin_enriched += 1
                print(f"LinkedIn✓", end=" ", flush=True)
            else:
                print(f"LinkedIn✗", end=" ", flush=True)
            time.sleep(random.uniform(2, 4))
        
        # 生成新的推荐理由
        new_recommendation = generate_recommendation(c, linkedin_info)
        new_score = compute_match_score(c, linkedin_info)
        
        # 更新
        c['background'] = new_recommendation
        c['match_score'] = new_score
        c['enriched'] = True
        c['enriched_at'] = datetime.now().isoformat()
        
        if linkedin_info.get('schools'):
            c['education'] = linkedin_info['schools']
        if linkedin_info.get('companies'):
            c['experience_history'] = linkedin_info['companies']
        if linkedin_info.get('skills'):
            c['skills_list'] = linkedin_info['skills']
        if linkedin_info.get('about'):
            c['about'] = linkedin_info['about']
        if linkedin_info.get('degrees'):
            c['degrees'] = linkedin_info['degrees']
        
        print(f"→ {new_score:.2f}")
        success += 1
    
    # 保存
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*50}")
    print(f"完成! 更新了 {success} 位候选人")
    print(f"LinkedIn信息获取成功: {linkedin_enriched}")
    print(f"数据库已保存: {DB_FILE}")


if __name__ == "__main__":
    main()
