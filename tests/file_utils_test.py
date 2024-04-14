from unittest.mock import patch, MagicMock
from app.utils.file_utils import *
from app.exceptions import *
import cProfile
import pstats
import io
import pytest


# @pytest.fixture(autouse=True)
# def profiler(request):
#     pr = cProfile.Profile()
#     pr.enable()
#     yield
#     pr.disable()
#     s = io.StringIO()
#     sortby = "cumulative"
#     ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
#     ps.print_stats()
#     print(s.getvalue())


@pytest.mark.asyncio
async def test_pdf_to_images_success():
    with patch("app.utils.file_utils.convert_from_bytes") as mock_convert:
        mock_image = MagicMock()
        mock_image.save = MagicMock()
        mock_convert.return_value = [mock_image]
        _, image_bytes = await pdf_to_images(b"sample_df_bytes")
        assert len(image_bytes) == 1


@pytest.mark.asyncio
async def test_pdf_to_images_success():
    with patch(
        "app.utils.file_utils.convert_from_bytes", side_effect=Exception("error")
    ):
        with pytest.raises(PDFToImageConversionError):
            await pdf_to_images(b"sample_pdf_bytes")


@pytest.mark.asyncio
async def test_pdf_to_images_with_multipage_native():
    with open("tests/test_files/multipage_native.pdf", "rb") as pdf_file:
        pdf_bytes = pdf_file.read()
    _, image_bytes = await pdf_to_images(pdf_bytes)
    assert len(image_bytes) > 0


@pytest.mark.asyncio
async def test_pdf_to_images_with_multipage_scanned():
    with open("tests/test_files/multipage_scanned.pdf", "rb") as pdf_file:
        pdf_bytes = pdf_file.read()
    _, image_bytes = await pdf_to_images(pdf_bytes)
    assert len(image_bytes) > 0


@pytest.mark.asyncio
async def test_pdf_to_images_with_singlepage_scanned():
    with open("tests/test_files/singlepage_scanned.pdf", "rb") as pdf_file:
        pdf_bytes = pdf_file.read()
    with pytest.raises(PDFToImageConversionError):
        _, image_bytes = await pdf_to_images(pdf_bytes)


@pytest.mark.asyncio
async def test_image_bytes_to_base64_success():
    sample_bytes = b"sample_image_data"
    with patch("base64.b64encode") as mock_base64_encode:
        mock_base64_encode.return_value = (
            b"c2FtcGxlX2ltYWdlX2RhdGE="  # base64 encoded string of 'sample_image_data'
        )
        result = await image_bytes_to_base64(sample_bytes)
        assert result == "c2FtcGxlX2ltYWdlX2RhdGE="


@pytest.mark.asyncio
async def test_image_bytes_to_base64_failure():
    sample_bytes = b"sample_image_data"
    with patch("base64.b64encode", side_effect=Exception("base64 encoding failed")):
        with pytest.raises(ImageProcessingError):
            await image_bytes_to_base64(sample_bytes)


@pytest.mark.asyncio
async def test_convert_audio_to_mp3_success():
    sample_bytes = b"sample_audio_data"
    with patch("pydub.AudioSegment.from_file") as mock_from_file:
        mock_audio_segment = MagicMock()
        mock_audio_segment.export = MagicMock()
        mock_from_file.return_value = mock_audio_segment
        file_type = "wav"
        _, mp3_data = await convert_audio_to_mp3(file_type, sample_bytes)
        assert mp3_data is not None


@pytest.mark.asyncio
async def test_convert_audio_to_mp3_failure():
    sample_bytes = b"sample_audio_data"
    file_type = "wav"
    with patch(
        "pydub.AudioSegment.from_file", side_effect=Exception("audio conversion failed")
    ):
        with pytest.raises(Exception) as exc_info:
            await convert_audio_to_mp3(file_type, sample_bytes)
        assert "audio conversion failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_convert_image_to_png_success():
    sample_bytes = b"sample_audio_data"
    file_type = "jpeg"
    with patch("PIL.Image.open") as mock_open:
        mock_image = MagicMock()
        mock_image.convert = MagicMock(return_value=mock_image)
        mock_image.save = MagicMock()
        mock_open.return_value = mock_image
        _, png_data = await convert_image_to_png(file_type, sample_bytes)
        assert png_data is not None


@pytest.mark.asyncio
async def test_convert_image_to_png_failure():
    sample_bytes = b"sample_audio_data"
    file_type = "jpeg"
    with patch("PIL.Image.open", side_effect=Exception("image conversion failed")):
        with pytest.raises(Exception) as exc_info:
            await convert_image_to_png(file_type, sample_bytes)
        assert "image conversion failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_convert_actual_audio_file_to_mp3():
    with open("tests/test_files/sample_audio.wav", "rb") as file:
        sample_bytes = file.read()
    file_type = "wav"
    _, mp3_data = await convert_audio_to_mp3(file_type, sample_bytes)
    assert mp3_data is not None
    assert isinstance(mp3_data, bytes)
    assert len(mp3_data) > 0


@pytest.mark.asyncio
async def test_convert_actual_image_file_to_png():
    with open("tests/test_files/sample_image.jpeg", "rb") as file:
        sample_bytes = file.read()
    file_type = "jpeg"
    _, png_data = await convert_image_to_png(file_type, sample_bytes)
    assert png_data is not None
    assert isinstance(png_data, bytes)
    assert len(png_data) > 0
