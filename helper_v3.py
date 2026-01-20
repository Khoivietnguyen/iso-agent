import json
import re
from pathlib import Path
import os

iso_overview = '''---
doc_id: ISO-IMPL-OVERVIEW
domain: iso
layer: overview
language: vi
authority_level: mandatory
children:
  - SEC-OVERVIEW
  - HR-OVERVIEW
---

# Tổng quan triển khai tiêu chuẩn ISO tại Công ty

## 1. Mục đích
Tài liệu này mô tả tổng thể việc triển khai các tiêu chuẩn ISO trong công ty,
bao gồm An toàn Thông tin (SEC) và Nhân sự (HR).

## 2. Phạm vi áp dụng
- Toàn bộ công ty
- Nhân viên, đối tác, nhà cung cấp
- Hệ thống thông tin và quy trình nhân sự

## 3. Cấu trúc triển khai
Triển khai ISO tại công ty bao gồm các nhóm chính:
- An toàn Thông tin (SEC – ISMS theo ISO/IEC 27001)
- Nhân sự (HR)

## 4. Nguyên tắc chung
- Ưu tiên tài liệu tiếng Việt
- Tuân thủ tiêu chuẩn ISO hiện hành
- Tài liệu phải có tính truy vết và nhất quán

## 5. Tài liệu liên quan
- SEC-OVERVIEW
- HR-OVERVIEW
'''

sec_overview = '''---
doc_id: SEC-OVERVIEW
domain: security
layer: overview
language: vi
authority_level: mandatory
rules:
  language_priority: vi
  conflict_rule: corporate_over_company
children:
  - security-handbooks
  - security-regulations
---

# Tổng quan triển khai An toàn Thông tin (ISMS)

## 1. Mục đích
Tài liệu này mô tả cách công ty triển khai hệ thống quản lý An toàn Thông tin
(ISMS) theo ISO/IEC 27001 và các tiêu chuẩn liên quan.

## 2. Nguyên tắc ưu tiên
- **Ưu tiên tài liệu tiếng Việt**
- **Khi có xung đột, tài liệu An toàn Thông tin cấp Tập đoàn (Corporate) có hiệu lực cao hơn tài liệu cấp Công ty**

## 3. Cấu trúc tài liệu An toàn Thông tin
Hệ thống tài liệu ISMS bao gồm:
- Sổ tay An toàn Thông tin (Corporate & Company)
- Quy định An toàn Thông tin
- Quy trình An toàn Thông tin
- Hướng dẫn thực hiện

## 4. Thứ tự áp dụng tài liệu
1. Corporate Security Handbook / Policy
2. Company Security Regulation
3. Security Process / Procedure
4. Security Guideline

## 5. Phạm vi áp dụng
- Nhân viên
- Đối tác / Nhà cung cấp
- Hệ thống CNTT

## 6. Tài liệu liên quan
(Tự động liên kết tới các tài liệu Security)
'''

hr_overview='''---
doc_id: HR-OVERVIEW
domain: hr
layer: overview
language: vi
authority_level: mandatory
children:
  - hr-processes
  - hr-job-descriptions
---

# Tổng quan triển khai tiêu chuẩn Nhân sự (HR)

## 1. Mục đích
Tài liệu này mô tả việc triển khai các quy trình và vai trò Nhân sự
theo tiêu chuẩn ISO và yêu cầu quản trị nội bộ của công ty.

## 2. Phạm vi áp dụng
- Bộ phận Nhân sự
- Các bộ phận liên quan
- Nhân viên công ty

## 3. Cấu trúc tài liệu HR
Hệ thống tài liệu HR bao gồm:
- Quy trình Nhân sự
- Mô tả công việc (Job Description)

## 4. Nguyên tắc áp dụng
- Quy trình HR phải được tuân thủ thống nhất
- Trách nhiệm được xác định rõ qua Job Description

## 5. Tài liệu liên quan
(Tự động liên kết tới các tài liệu HR)
'''


SEC_HB_CORP_TEMPLATE = """---
doc_id: {doc_id}
domain: security
layer: handbook
scope: corporate
doc_class: {doc_class}
metadata: {metadata}
language: {lang}
authority_level: mandatory
applicability: group-wide
related_regulations: auto
---
"""

SEC_HB_COMPANY_TEMPLATE = """---
doc_id: {doc_id}
domain: security
layer: handbook
scope: company
metadata: {metadata}
language: vi
priority: company 
---
"""

SEC_REG_TEMPLATE = """---
doc_id: {doc_id}
domain: security
layer: regulation
metadata: {metadata}
language: {lang}
children: {children}
---
"""

SEC_PROCESS_TEMPLATE = """---
doc_id: {doc_id}
domain: security
layer: process
parent_regulation: {parent_regulation}
language: {lang}
execution_level: operational
---
"""

SEC_GUIDELINE_TEMPLATE = """---
doc_id: {doc_id}
domain: security
layer: guideline
parent_regulation: {parent_regulation}
language: {lang}
authority_level: advisory
---
"""

SEC_REG_HB_TEMPLATE = """---
doc_id: {doc_id}
domain: security
layer: handbook
scope: corporate,
metadata: business-continuity-governance
language: en
linked_regulation: {parent_regulation}
authoritative: true
---
"""

JD_TEMPLATE = """---
doc_id: {doc_id}
domain: hr
layer: job-description
language: en
authority_level: mandatory
---
"""

HR_PROCESS_TEMPLATE = """---
doc_id: {doc_id}
domain: hr
layer: process
metadata: {metadata}
language: {lang}
authority_level: mandatory
---
"""

Additional_HANDBOOKS = [
]


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"(ntt data(,| inc\.?)?)|cs-[a-z]{2}-\d+", "", text)
    text = re.sub(r"v\d+\.\d+", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")

def classify_doc(name: str) -> str:
    n = name.lower()
    if "policy" in n:
        return "policy"
    if "standard" in n:
        return "standard"
    if "procedure" in n or "plan" in n:
        return "procedure"
    if "framework" in n:
        return "framework"
    if "whitepaper" in n:
        return "whitepaper"
    if "infographic" in n:
        return "infographic"
    return "document"

def generate_doc_id(name: str) -> str:
    base = normalize(name.replace(".md", ""))
    tokens = base.split("-")[:6]
    return "SEC-HB-CORP-" + "-".join(t.upper() for t in tokens)

def read_json(path=''):
    try:        
        with open(path, 'r', encoding='utf-8') as file:            
            data = json.load(file)
            return data
    except Exception as e:
        print(e)

def process_additional_handbooks(out_dir='rag_v5/security/handbooks/corporate'):
    OUTPUT_DIR = Path(f"{out_dir}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for fname in Additional_HANDBOOKS:
        doc_id = generate_doc_id(fname)
        output_file = OUTPUT_DIR / f"{doc_id}.md"
        if output_file.exists():
            print(f"SKIP: {output_file.name}")
            continue
        print('Creating file', str(output_file))
        filename = '01. Chính sách và Sổ tay ATTT\\' + fname
        if not os.path.exists(filename):
            print(f'\tNo input file {filename}, skipping')
            continue 
        
        with open(filename, 'r', encoding='utf-8') as original_file:
            content = original_file.read()
        new_content = SEC_HB_CORP_TEMPLATE.format(
            doc_id=doc_id,
            doc_class=classify_doc(fname),
            metadata=normalize(fname.replace(".md", "")).replace("-", " "),
            title=fname.replace(".md", "")
        )  + '\n\n' + content
        output_file.write_text(new_content, encoding='utf-8')

def create_output_file(name, header, content, out_dir='rag_v5'):
    OUTPUT_DIR = Path(f"{out_dir}") 
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / name
    # check output
    if output_file.exists():
        print(f"\tSKIP: {output_file.name}")
    if header is not None:
        output_file.write_text(header + '\n\n' + content, encoding='utf-8')
    else:
        output_file.write_text(content, encoding='utf-8')

def process_corp_handbooks(handbook, out_dir='rag_v5', input_dir='out_dir'):
    corperate_handbooks = handbook['corporate']    
    for handbook in corperate_handbooks:
        if not os.path.exists(input_dir + '\\' + handbook['input']):
            print(f'\tNo input file {handbook['input']}, skipping')
            continue        
        header = SEC_HB_CORP_TEMPLATE.format(
            doc_id=handbook['output'].replace(".md", ""),
            doc_class='standard',
            metadata=handbook['metadata'],
            lang=handbook['lang']           
        )           
        # print(header)
        with open(input_dir + '\\' + handbook['input'], 'r', encoding='utf-8') as original_file:
            content = original_file.read()
        create_output_file(handbook['output'], header, content, out_dir=out_dir)

def process_comp_handbooks(handbook, out_dir='rag_v5', input_dir='out_dir'):
     company_handbooks =  handbook['company']
     for handbook in company_handbooks:
        if not os.path.exists(input_dir + '\\' + handbook['input']):
            print(f'\tNo input file {handbook['input']}, skipping')
            continue
        header = SEC_HB_COMPANY_TEMPLATE.format(
            doc_id=handbook['output'].replace(".md", ""),
            doc_class='standard',
            metadata=handbook['metadata'],                    
        )
        with open(input_dir + '\\' + handbook['input'], 'r', encoding='utf-8') as original_file:
            content = original_file.read()
        create_output_file(handbook['output'], header, content, out_dir=out_dir)
         

def process_regulations(regulations, out_dir='rag_v5', input_dir='out_dir'):     
    for regulation_items in regulations.values():
        for regulation in regulation_items:        
            if "mock" in regulation:
                reg_intput_content = regulation['input']
            elif os.path.exists(input_dir + '\\'+ regulation['input']):
                with open(input_dir + '\\' + regulation['input'], 'r', encoding='utf-8') as original_file:
                    reg_intput_content = original_file.read()
            else:
                print(f'\tNo input file {regulation['input']}, skipping')
                continue
            # regulation ID in case it has processes and guideline
            regulation_id = regulation['output'].replace(".md", "")
            reg_children = ''           
            process_contents = []
            guilde_contents = []
            handbook_contents = []
           
            if "processes" in regulation:
                # print(f'{regulation_id} has  processes')
                for process in regulation['processes']:
                    process_header = SEC_PROCESS_TEMPLATE.format(
                        doc_id=process['output'].replace(".md", ""),           
                        parent_regulation=regulation_id,   
                        lang='vi'                        
                    )
                    process_contents.append({
                        'name': process['output'],
                        'header': process_header,
                        'input': process['input']
                    })
                    reg_children += '\n- ' +  process['output'].replace(".md", "")

            if "guidelines" in regulation:
                # print(f'{regulation_id} has  guidelines')
                for guideline in regulation['guidelines']:
                    guideline_header = SEC_GUIDELINE_TEMPLATE.format(
                        doc_id=guideline['output'].replace(".md", ""),           
                        parent_regulation=regulation_id,   
                        lang='vi'                        
                    )
                    guilde_contents.append({
                        'name': guideline['output'],
                        'header': guideline_header,
                        'input': guideline['input']
                    })
                    reg_children += '\n- ' +  guideline['output'].replace(".md", "")

            if "handbooks" in regulation:
                for handbook in regulation['handbooks']:
                    handbook_header = SEC_REG_HB_TEMPLATE .format(
                        doc_id=handbook['output'].replace(".md", ""),           
                        parent_regulation=regulation_id                                            
                    )
                    handbook_contents.append({
                        'name': handbook['output'],
                        'header': handbook_header,
                        'input': handbook['input']
                    })
                    reg_children += '\n- ' +  handbook['output'].replace(".md", "")

            
            if len(process_contents) > 0:
                for process_info in process_contents:
                    if not os.path.exists(input_dir + '\\'+ process_info['input']):
                        print(f'\tNo input file {process_info['input']}, skipping')
                        continue
                    with open(input_dir + '\\' + process_info['input'], 'r', encoding='utf-8') as original_file:
                        intput_content = original_file.read()
                    create_output_file(process_info['name'], process_info['header'], intput_content, out_dir=out_dir)
                    

            if len(guilde_contents) > 0:
                for guilde_info in guilde_contents:
                    if not os.path.exists(input_dir + '\\'+ guilde_info['input']):
                        print(f'\tNo input file {guilde_info['input']}, skipping')
                        continue
                    with open(input_dir + '\\' + guilde_info['input'], 'r', encoding='utf-8') as original_file:
                        intput_content = original_file.read()
                    create_output_file(guilde_info['name'], guilde_info['header'], intput_content, out_dir=out_dir)
            if len(handbook_contents) > 0:
                for hb_info in handbook_contents:
                    if not os.path.exists(input_dir + '\\'+ hb_info['input']):
                        print(f'\tNo input file {hb_info['input']}, skipping')
                        continue
                    with open(input_dir + '\\' + hb_info['input'], 'r', encoding='utf-8') as original_file:
                        intput_content = original_file.read()
                    create_output_file(hb_info['name'], hb_info['header'], intput_content, out_dir=out_dir)

            # create regulation
            reg_header = SEC_REG_TEMPLATE.format(
                doc_id=regulation_id,           
                metadata=regulation['metadata'],   
                lang=regulation['lang'],  
                children=reg_children
            )
            create_output_file(regulation['output'], reg_header, reg_intput_content,out_dir=out_dir)


def process_hr(hrcontent, out_dir='rag_v4/hr/', input_dir='out_dir'):      
    # process JD
    jd_contents = []    
    job_list = hrcontent['job_description']
    for jd in job_list:
        jd_header = JD_TEMPLATE.format(
            doc_id=jd['output'].replace(".md", ""),                                   
        )
        jd_contents.append({
            'name': jd['output'],
            'header': jd_header,
            'input': jd['input']
        })
        
    # print(jd_contents)
    # process HR process
    hr_content=[]
    process_list = hrcontent['processes']
    for process in process_list:
        process_header = HR_PROCESS_TEMPLATE.format(
            doc_id=process['output'].replace(".md", ""), 
            metadata=process['metadata'],
            lang=process['lang']                           
        )
        hr_content.append({
            'name': process['output'],
            'header': process_header,
            'input': process['input']
        })

    # print(hr_content)
    if len(jd_contents) > 0:
        for jd_info in jd_contents:
            if not os.path.exists(input_dir + '\\'+ jd_info['input']):
                print(f'\tNo input file {jd_info['input']}, skipping')
                continue
            with open(input_dir + '\\' + jd_info['input'], 'r', encoding='utf-8') as original_file:
                intput_content = original_file.read()
            create_output_file(jd_info['name'], jd_info['header'], intput_content, out_dir=out_dir)
    
    if len(hr_content) > 0:
        for hr_info in hr_content:
            if not os.path.exists(input_dir + '\\'+ hr_info['input']):
                print(f'\tNo input file {hr_info['input']}, skipping')
                continue
            with open(input_dir + '\\' + hr_info['input'], 'r', encoding='utf-8') as original_file:
                intput_content = original_file.read()
            create_output_file(hr_info['name'], hr_info['header'], intput_content, out_dir=out_dir)


if __name__ == "__main__":
    print(f'Processing {len(Additional_HANDBOOKS)} additional handbooks')
    print('Creating overviews')
    create_output_file('ISO-IMPLEMENTATION-OVERVIEW.md', None, iso_overview, out_dir='rag_v5/')
    create_output_file('SEC-OVERVIEW.md', None, sec_overview, out_dir='rag_v5/')
    create_output_file('HR-OVERVIEW.md', None, hr_overview, out_dir='rag_v5/')

    config_path = 'iso-implementation.json'
    json_content = read_json(path=config_path)
    if json_content is None:
        print('Cannot read file', config_path)
        exit(1)
    print('Creating corporate handbooks')
    process_corp_handbooks(json_content['security']['handbooks'], out_dir='rag_v5/security/handbooks')
    print('Creating company handbooks')
    process_comp_handbooks(json_content['security']['handbooks'], out_dir='rag_v5/security/handbooks')
    print('Creating security regulations/policies/guidelines')
    process_regulations(json_content['security']['regulations'], out_dir='rag_v5/security/regulations')
    print('Creating HR processes')
    process_hr(json_content['hr'],  out_dir='rag_v5/hr')