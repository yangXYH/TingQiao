import asyncio
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

APP = Path(__file__).resolve().parent.parent / 'app'
sys.path.insert(0, str(APP))
import batch_export
import server


class FakeRequest:
    def __init__(self, body):
        self.body = body

    async def json(self):
        return self.body


class ArchiveTests(unittest.TestCase):
    def test_ids_are_validated_and_deduplicated(self):
        self.assertEqual(batch_export.validate_record_ids(['a' * 32, 'a' * 32]), ['a' * 32])
        for value in (None, [], 'all', ['../private'], [None], ['a' * 32] * 201):
            with self.subTest(value=type(value).__name__), self.assertRaises(ValueError):
                batch_export.validate_record_ids(value)

    def test_portable_unique_chinese_filenames_and_analysis_only(self):
        records = [dict(title='../同名:分析', analysis='# 摘要\n第一份'), dict(title='../同名:分析', analysis='# 摘要\n第二份'), dict(title='较长标题' * 90, analysis='结论')]
        blob = batch_export.make_analysis_zip(records)
        with zipfile.ZipFile(BytesIO(blob)) as archive:
            names = archive.namelist()
            self.assertEqual(len(set(names)), 3)
            for name in names:
                self.assertEqual(PurePosixPath(name).name, name)
                self.assertNotIn(':', name)
                self.assertLess(len(name.encode('utf-8')), 255)
                self.assertTrue(name.endswith('.md'))
            self.assertEqual(archive.read(names[0]).decode('utf-8'), records[0]['analysis'] + '\n')
            self.assertEqual(archive.read(names[1]).decode('utf-8'), records[1]['analysis'] + '\n')

    def test_empty_or_oversized_documents_do_not_create_partial_archives(self):
        with self.assertRaises(ValueError):
            batch_export.make_analysis_zip([dict(title='尚未完成', analysis=' ')])
        with patch.object(batch_export, 'MAX_EXPORT_BYTES', 8), self.assertRaises(ValueError):
            batch_export.make_analysis_zip([dict(title='测试', analysis='content longer than limit')])


class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = patch.object(server, 'DB', Path(self.temp.name) / 'archive.sqlite3')
        self.database.start()
        self.addCleanup(self.database.stop)
        self.addCleanup(self.temp.cleanup)
        server.initialize_db()
        with server.db() as con:
            for index, analysis, state in [(1, '# 测试结论\n已确认。[00:05]', 'ready'), (2, '# 上次分析\n已保存内容', 'analyzing'), (3, '', 'transcribing')]:
                con.execute('INSERT INTO recordings(id,title,original_name,file_name,size,created_at,updated_at,status,analysis,transcript) VALUES(?,?,?,?,?,?,?,?,?,?)',
                            (str(index) * 32, '同名测试', 'sample.wav', 'sample.wav', 1, server.now(), server.now(), state, analysis,
                             json.dumps([dict(start=0, end=1, text='原文不应出现在批量文档')], ensure_ascii=False)))

    def export(self, ids):
        return asyncio.run(server.batch_export_recordings(FakeRequest({'ids': ids})))

    def test_endpoint_keeps_selection_order_removes_citations_and_omits_transcript(self):
        response = self.export(['2' * 32, '1' * 32, '2' * 32])
        self.assertEqual(response.media_type, 'application/zip')
        self.assertEqual(response.headers['cache-control'], 'no-store')
        with zipfile.ZipFile(BytesIO(response.body)) as archive:
            names = archive.namelist()
            self.assertEqual(len(names), 2)
            self.assertIn('上次分析', archive.read(names[0]).decode('utf-8'))
            content = archive.read(names[1]).decode('utf-8')
            self.assertNotIn('[00:05]', content)
            self.assertNotIn('原文不应出现在批量文档', content)

    def test_missing_or_unfinished_records_fail_without_partial_download(self):
        for ids, status in [(['1' * 32, 'f' * 32], 404), (['1' * 32, '3' * 32], 400), ([], 400)]:
            with self.subTest(status=status), self.assertRaises(server.HTTPException) as exc:
                self.export(ids)
            self.assertEqual(exc.exception.status_code, status)

    def test_list_exposes_eligibility_without_analysis_body(self):
        items = {row['id']: row for row in server.list_recordings()['items']}
        self.assertTrue(items['1' * 32]['has_analysis'])
        self.assertTrue(items['2' * 32]['has_analysis'])
        self.assertFalse(items['3' * 32]['has_analysis'])
        self.assertNotIn('analysis', items['1' * 32])


if __name__ == '__main__':
    unittest.main()
