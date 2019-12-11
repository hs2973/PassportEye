'''
PassportEye::Util: PDF processing utilities.

Author: Konstantin Tretyakov
License: MIT
'''
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTFigure, LTImage

try:
    from pdfminer.pdfparser import PDFParser, PDFDocument, PDFPage
except ImportError:
    from pdfminer.pdfparser import PDFParser
    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.pdfpage import PDFPage


def extract_jpegs_from_pdf(fstream):
    """
    Reads a given PDF file and scans for the first valid embedded JPEG image.
    Returns either None (if none found) or a string of data for the image.
    There is no 100% guarantee for this code, yet it seems to work fine with most
    scanner-produced images around.
    More testing might be needed though.

    Note that in principle there is no serious problem extracting PNGs or other image types from PDFs,
    however at the moment I do not have enough test data to try this, and the one I have seems to be unsuitable
    for PDFMiner.

    :param fstream: Readable binary stream of the PDF
    :return: binary stream, containing the whole contents of the JPEG image or None if extraction failed.
    """
    parser = PDFParser(fstream)
    try:
        document = PDFDocument()
        parser.set_document(document)
        document.set_parser(parser)
        document.initialize('')
    except TypeError:
        document = PDFDocument(parser)
    rsrcmgr = PDFResourceManager()
    device = PDFPageAggregator(rsrcmgr)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    try:
        pages = document.get_pages()
    except Exception:
        pages = PDFPage.create_pages(document)
    for page in pages:
        interpreter.process_page(page)
        layout = device.result
        for el in layout:
            if isinstance(el, LTFigure):
                for im in el:
                    if isinstance(im, LTImage):
                        # Found one!
                        try:
                            imdata = im.stream.get_data()
                        except Exception:
                            # Failed to decode (seems to happen nearly always - there's probably a bug in PDFMiner), oh well...
                            imdata = im.stream.get_rawdata()
                        if imdata is not None and imdata.startswith(b'\xff\xd8\xff\xe0'):
                            yield imdata

    return None


def extract_first_jpeg_in_pdf(fstream):
    return next(extract_jpegs_from_pdf(fstream), None)
