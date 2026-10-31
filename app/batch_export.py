"""Create a portable archive containing saved analysis documents only."""
from io import BytesIO
import re
import zipfile

MAX_BATCH_EXPORT = 200
MAX_EXPORT_BYTES = 32 * 1024 * 1024


def validate_record_ids(value):
    if not isinstance(value, list) or not value:
        raise ValueError('请先选择需要下载的录音')
    if len(value) > MAX_BATCH_EXPORT:
        raise ValueError(f'单次最多下载 {MAX_BATCH_EXPORT} 份分析，请分批选择')
    if any(not isinstance(item, str) or not re.fullmatch(r'[a-f0-9]{32}', item) for item in value):
        raise ValueError('录音标识无效，请刷新档案后重新选择')
    return list(dict.fromkeys(value))


def analysis_filename(title, number, width):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f]', '_', str(title or '')).strip(' .')
    # Limit UTF-8 bytes as well as characters for Chinese filenames on macOS.
    name = name.encode('utf-8')[:160].decode('utf-8', errors='ignore').rstrip(' .') or '录音分析'
    return f'{number:0{width}d}_{name}.md'


def make_analysis_zip(records):
    if not records or len(records) > MAX_BATCH_EXPORT:
        raise ValueError('请选择 1 至 200 份分析文档')
    documents, size = [], 0
    width = max(2, len(str(len(records))))
    for index, record in enumerate(records, 1):
        analysis = str(record.get('analysis') or '').strip()
        if not analysis:
            raise ValueError('所选录音中有尚未生成分析的项目，请刷新后重新选择')
        content = (analysis + '\n').encode('utf-8')
        size += len(content)
        if size > MAX_EXPORT_BYTES:
            raise ValueError('所选分析文档过大，请减少数量后分批下载')
        documents.append((analysis_filename(record.get('title'), index, width), content))
    output = BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for filename, content in documents:
            archive.writestr(filename, content)
    return output.getvalue()
