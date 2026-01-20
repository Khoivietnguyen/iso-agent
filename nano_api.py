import requests
import time

API_KEY = 'api-key'
BASE_URL = 'https://extraction-api.nanonets.com/api/v1'


def pdf_2_markdown(path=''):
    API_KEY = "api-key" 
    # url = "https://extraction-api.nanonets.com/extract"
    url = "https://extraction-api.nanonets.com/api/v1/extract/async"
    files = {"file": open(path, "rb")}
    data = {
        "output_format": "markdown",
        # "ocr_enabled": True,
        # 'preserve_layout': True,
        # 'include_images': True
    }
     
    headers = {"Authorization": f"Bearer {API_KEY}"}
    # headers = {"Authorization": API_KEY}
    try:
        resp = requests.post(url, headers=headers, files=files, data=data, timeout=300)   
        result = resp.json()    
        print(result)
        markdown = result["result"]["markdown"]["content"]
        with open("output1.md", "w", encoding="utf-8") as f:
            f.write(markdown)
    except Exception as e:
        print(e)


def async_extract(file_path=''):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    with open(file_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/extract/async",
            headers=headers,
            files={"file": f},
            data={"output_format": "markdown"}
        )
    
    response.raise_for_status()
    return response.json()["record_id"]


def poll_result(record_id, max_wait=300, interval=5):
    """Poll for async extraction result."""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    start = time.time()
    
    while time.time() - start < max_wait:
        response = requests.get(
            f"{BASE_URL}/extract/results/{record_id}",
            headers=headers
        )
        result = response.json()
        
        if result["status"] == "completed":
            return result
        elif result["status"] == "failed":
            raise Exception(f"Extraction failed: {result['message']}")
        
        time.sleep(interval)
    
    raise TimeoutError("Extraction timed out")


def pdf_2_markdown_async(file_path=''):
    record_id = async_extract(file_path)
    result = poll_result(record_id)
    markdown = result["result"]["markdown"]["content"]
    with open("output1.md", "w", encoding="utf-8") as f:
        f.write(markdown)

def pdf_2_markdown_batch():
    headers = {"Authorization": f"Bearer {API_KEY}"}    
    file_paths = ['./CS-ST-02-Acceptable Use of IT Assets Security Standard-VN.pdf', './CS-ST-02-Acceptable Use of IT Assets Security Standard-EN.pdf']   
   

    files_to_upload = [('files', open(file_path, 'rb')) for file_path in file_paths]
    
    try:
        resp = requests.post(f"{BASE_URL}/extract/batch", 
                             headers=headers, 
                             files=files_to_upload,
                             data={"output_format": "markdown"}
                             )   
        result = resp.json()    
        print(result)        
    except Exception as e:
        print(e)


def manual_get_resuts():
    job_ids = [1855835]
    for i, record_id in enumerate(job_ids):
        print('Processing', i, record_id)
        result = poll_result(record_id)
        # print(result)
        markdown = result["result"]["markdown"]["content"]
        with open("output_{}.md".format(i), "w", encoding="utf-8") as f:
            f.write(markdown)


if __name__ == '__main__':
    # pdf_2_markdown('./CS-ST-02-Acceptable Use of IT Assets Security Standard-VN.pdf')
    print('Converting PDF to markdown')
    manual_get_resuts()
    # pdf_2_markdown_batch()
    # pdf_2_markdown_async('./CS-ST-02-Acceptable Use of IT Assets Security Standard-VN.pdf')