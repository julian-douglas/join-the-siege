from quart import Quart, request, jsonify
from src.classifier import classify_file
import logging
import asyncio

app = Quart(__name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'heic', 'docx', 'xlsx', 'csv'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB file size limit


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_within_size_limit(file):
    return len(file.read()) <= MAX_FILE_SIZE

@app.route('/classify_file', methods=['POST'])
async def handle_classify_file():
    try:
        files = await request.files
        
        files_to_process = files.getlist('file')
        
        if not files_to_process:
            return jsonify({"error": "No files provided"}), 400

        logger.debug(f"Received {len(files_to_process)} files to process")
        
        valid_files = []
        for file in files_to_process:
            if file.filename == '':
                continue
            if not allowed_file(file.filename):
                logger.warning(f"Skipping file with unsupported type: {file.filename}")
                continue
            if not is_within_size_limit(file):
                logger.error(f"Skipping file due to size limit: {file.filename}")
                return jsonify({'error': f'File exceeds the maximum allowed size of {MAX_FILE_SIZE / 1024 / 1024} MB'}), 400

            valid_files.append(file)

        if not valid_files:
            return jsonify({"error": "No valid files to process"}), 400

        logger.debug(f"Processing {len(valid_files)} valid files")
        
        # Process all files concurrently
        tasks = []
        for file in valid_files:
            logger.debug(f"Creating task for file: {file.filename}")
            task = asyncio.create_task(process_single_file(file))
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Format the results
        formatted_results = {}
        for file, result in zip(valid_files, results):
            if isinstance(result, Exception):
                formatted_results[file.filename] = {"error": str(result)}
            else:
                formatted_results[file.filename] = {"result": result}
            logger.debug(f"Result for {file.filename}: {result}")

        return jsonify(formatted_results)

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500

async def process_single_file(file):
    try:
        logger.debug(f"Starting classification for file: {file.filename}")
        result = await classify_file(file)
        logger.debug(f"Completed classification for file: {file.filename} with result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
        raise

if __name__ == '__main__':
    app.run(debug=True)
