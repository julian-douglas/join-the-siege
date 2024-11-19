import pytest
from io import BytesIO
import asyncio
import io
from werkzeug.datastructures import FileStorage
from src.app import app, allowed_file

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@pytest.fixture
def test_app():
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(test_app):
    return test_app.test_client()  

@pytest.mark.parametrize("filename, expected", [
    ("file.pdf", True),
    ("file.png", True),
    ("file.jpg", True),
    ("file.docx", True),
    ("file.JPEG", True),
    ("file.xlsx", True),
    ("file.txt", False),
    ("file", False),
])
def test_allowed_file(filename, expected):
    assert allowed_file(filename) == expected

@pytest.mark.asyncio
async def test_no_file_in_request(client):
    response = await client.post('/classify_file')
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_no_selected_file(client):
    data = {'file': (BytesIO(b""), '')}
    response = await client.post('/classify_file', form={'file': data})
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_success(client, mocker):
    async def mock_classify(*args, **kwargs):
        return 'test_class'
    
    mocker.patch('src.app.classify_file', side_effect=mock_classify)

    file_data = io.BytesIO(b"dummy content")
    file_storage = FileStorage(stream=file_data, filename='file.pdf', content_type='application/pdf')
    
    response = await client.post('/classify_file', files={'file': file_storage})
    
    print(f"Response status: {response.status_code}")
    print(f"Response data: {await response.get_json()}")
    
    assert response.status_code == 200
    response_data = await response.get_json()
    assert 'file.pdf' in response_data
    assert response_data['file.pdf']['result'] == 'test_class'

@pytest.mark.asyncio
async def test_multiple_requests_at_once(client, mocker):
    async def mock_classify(*args, **kwargs):
        return 'test_class'
    
    mocker.patch('src.app.classify_file', side_effect=mock_classify)

    file1_data = io.BytesIO(b"dummy content 1")
    file1_storage = FileStorage(stream=file1_data, filename='file1.pdf', content_type='application/pdf')

    file2_data = io.BytesIO(b"dummy content 2")
    file2_storage = FileStorage(stream=file2_data, filename='file2.JPEG', content_type='image/jpeg')

    file3_data = io.BytesIO(b"dummy content 3")
    file3_storage = FileStorage(stream=file3_data, filename='file3.docx', content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

    responses = await asyncio.gather(
        client.post('/classify_file', files={'file': file1_storage}),
        client.post('/classify_file', files={'file': file2_storage}),
        client.post('/classify_file', files={'file': file3_storage})
    )

    for i, response in enumerate(responses, 1):
        assert response.status_code == 200
        response_data = await response.get_json()
        filename = f'file{i}.{"pdf" if i == 1 else "JPEG" if i == 2 else "docx"}'
        assert filename in response_data
        assert response_data[filename]['result'] == 'test_class'

@pytest.mark.asyncio
async def test_file_size_limit(client, mocker):
    # Mock the classify_file function
    async def mock_classify(*args, **kwargs):
        return 'test_class'
    
    mocker.patch('src.app.classify_file', side_effect=mock_classify)

    large_file_data = io.BytesIO(b"a" * (MAX_FILE_SIZE + 1024))  # 10 MB + 1 KB
    large_file_storage = FileStorage(stream=large_file_data, filename='large_file.pdf', content_type='application/pdf')

    response = await client.post('/classify_file', files={'file': large_file_storage})

    assert response.status_code == 400
    response_data = await response.get_json()
    
    assert response_data['error'] == f'File exceeds the maximum allowed size of {MAX_FILE_SIZE / 1024 / 1024} MB'


@pytest.mark.asyncio
async def test_file_within_size_limit(client, mocker):
    async def mock_classify(*args, **kwargs):
        return 'test_class'
    
    mocker.patch('src.app.classify_file', side_effect=mock_classify)

    small_file_data = io.BytesIO(b"a" * (5 * 1024 * 1024))  # 5 MB
    small_file_storage = FileStorage(stream=small_file_data, filename='small_file.pdf', content_type='application/pdf')

    response = await client.post('/classify_file', files={'file': small_file_storage})

    assert response.status_code == 200
    response_data = await response.get_json()
    
    assert 'small_file.pdf' in response_data
    assert response_data['small_file.pdf']['result'] == 'test_class'
