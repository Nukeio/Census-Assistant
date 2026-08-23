"""
Census Assistant - Ingestion Pipeline
Parses Excel source sheets (Functionaries & HLB Allocations) and PDF manuals into structured tables and FTS search indices.
"""

import os
import re
import logging
from datetime import datetime
import openpyxl
import pypdf
from .database import get_db_connection, init_database

logger = logging.getLogger("IngestionEngine")
logging.basicConfig(level=logging.INFO)

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
# Admin-uploaded replacement files live in DATA_DIR (the persistent volume in
# production); the original seed copies baked into the image/repo live in
# ROOT_DIR. Always prefer a newer DATA_DIR copy if one has been uploaded.
DATA_DIR = os.environ.get("DATA_DIR", ROOT_DIR)

def _resolve_source(filename: str) -> str:
    data_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(data_path):
        return data_path
    return os.path.join(ROOT_DIR, filename)

def ingest_all_users(filepath: str = None) -> int:
    """Ingest All_Users.xlsx into functionaries table."""
    if not filepath:
        filepath = _resolve_source("All_Users.xlsx")
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}")
        return 0

    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb.active

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM functionaries")
    try:
        cursor.execute("DELETE FROM functionaries_fts")
    except Exception:
        pass

    inserted = 0
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not row or not any(row):
            continue
        sno = row[0] if len(row) > 0 else None
        user_id = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""
        if not user_id:
            continue
        func_type = str(row[2]).strip() if len(row) > 2 and row[2] is not None else ""
        name = str(row[3]).strip() if len(row) > 3 and row[3] is not None else ""
        mobile = str(row[4]).strip().replace(".0", "") if len(row) > 4 and row[4] is not None else ""
        state_ut = str(row[5]).strip() if len(row) > 5 and row[5] is not None else ""
        district = str(row[6]).strip() if len(row) > 6 and row[6] is not None else ""
        sub_district = str(row[7]).strip() if len(row) > 7 and row[7] is not None else ""
        village_town = str(row[8]).strip() if len(row) > 8 and row[8] is not None else ""
        status = str(row[9]).strip() if len(row) > 9 and row[9] is not None else "ACTIVE"

        cursor.execute("""
            INSERT OR REPLACE INTO functionaries 
            (sno, user_id, functionary_type, name, mobile_number, state_ut, district, sub_district, village_town, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (sno, user_id, func_type, name, mobile, state_ut, district, sub_district, village_town, status))

        row_id = cursor.lastrowid
        try:
            cursor.execute("""
                INSERT INTO functionaries_fts (rowid, user_id, functionary_type, name, mobile_number, district, sub_district)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (row_id, user_id, func_type, name, mobile, district, sub_district))
        except Exception:
            pass

        inserted += 1

    conn.commit()
    conn.close()
    logger.info(f"Ingested {inserted} functionaries from {filepath}")
    return inserted


def ingest_hlb_allocation(filepath: str = None) -> int:
    """Ingest HLB Allocation (2).xlsx into hlb_allocations table."""
    if not filepath:
        filepath = _resolve_source("HLB Allocation (2).xlsx")
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}")
        return 0

    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb.active

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM hlb_allocations")
    try:
        cursor.execute("DELETE FROM hlb_allocations_fts")
    except Exception:
        pass

    inserted = 0
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not row or not any(row):
            continue
        circle_no = str(row[0]).strip() if len(row) > 0 and row[0] is not None else ""
        hlb_no = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""
        if not hlb_no and not circle_no:
            continue
        sup_name = str(row[2]).strip() if len(row) > 2 and row[2] is not None else ""
        enum_name = str(row[3]).strip() if len(row) > 3 and row[3] is not None else ""
        enum_user_id = str(row[4]).strip() if len(row) > 4 and row[4] is not None else ""
        allot_date = str(row[5]).strip() if len(row) > 5 and row[5] is not None else ""

        cursor.execute("""
            INSERT INTO hlb_allocations 
            (supervisory_circle_no, hlb_no, supervisor_name, enumerator_name, enumerator_user_id, allotment_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (circle_no, hlb_no, sup_name, enum_name, enum_user_id, allot_date))

        row_id = cursor.lastrowid
        try:
            cursor.execute("""
                INSERT INTO hlb_allocations_fts (rowid, supervisory_circle_no, hlb_no, supervisor_name, enumerator_name, enumerator_user_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (row_id, circle_no, hlb_no, sup_name, enum_name, enum_user_id))
        except Exception:
            pass

        inserted += 1

    conn.commit()
    conn.close()
    logger.info(f"Ingested {inserted} HLB allocations from {filepath}")
    return inserted


def ingest_pdf_manuals() -> int:
    """Ingest FAQ and HLO manuals into manual_chunks with section and page mapping."""
    pdf_files = [
        {
            "filename": "FAQ (E & S).c58cf9c49a6df89a94b3 (1).pdf",
            "doc_title": "Census 2027 FAQ for Enumerators and Supervisors",
            "source_type": "FAQ"
        },
        {
            "filename": "HLO_Manual_English.pdf",
            "doc_title": "House Listing Operations (HLO) Instruction Manual",
            "source_type": "Manual"
        }
    ]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM manual_chunks")
    try:
        cursor.execute("DELETE FROM manual_chunks_fts")
    except Exception:
        pass
    conn.commit()

    total_chunks = 0

    for pdf_info in pdf_files:
        filepath = _resolve_source(pdf_info["filename"])
        if not os.path.exists(filepath):
            logger.warning(f"PDF file not found: {filepath}")
            continue

        logger.info(f"Parsing PDF: {pdf_info['filename']}...")
        try:
            reader = pypdf.PdfReader(filepath)
            num_pages = len(reader.pages)
            for page_num, page in enumerate(reader.pages, start=1):
                try:
                    text = page.extract_text() or ""
                except Exception as e:
                    logger.warning(f"Error reading page {page_num} in {pdf_info['filename']}: {e}")
                    continue

                if not text.strip():
                    continue

                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                if not paragraphs:
                    paragraphs = [text.strip()]

                current_chunk = ""
                current_header = ""

                for p in paragraphs:
                    header_match = re.match(r'^(Q\.\s*\d+|Question\s*\d+|Chapter\s*\d+|\d+\.\d+|\b[A-Z\s]{4,}\b)', p)
                    if header_match:
                        current_header = header_match.group(0)

                    if len(current_chunk) + len(p) < 800:
                        current_chunk += ("\n\n" + p) if current_chunk else p
                    else:
                        if current_chunk.strip():
                            cursor.execute("""
                                INSERT INTO manual_chunks (source_file, doc_title, page_number, section_header, chunk_text)
                                VALUES (?, ?, ?, ?, ?)
                            """, (pdf_info["filename"], pdf_info["doc_title"], page_num, current_header, current_chunk.strip()))
                            row_id = cursor.lastrowid
                            try:
                                cursor.execute("""
                                    INSERT INTO manual_chunks_fts (rowid, source_file, doc_title, page_number, section_header, chunk_text)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (row_id, pdf_info["filename"], pdf_info["doc_title"], str(page_num), current_header, current_chunk.strip()))
                            except Exception:
                                pass
                            total_chunks += 1
                        current_chunk = p

                if current_chunk.strip():
                    cursor.execute("""
                        INSERT INTO manual_chunks (source_file, doc_title, page_number, section_header, chunk_text)
                        VALUES (?, ?, ?, ?, ?)
                    """, (pdf_info["filename"], pdf_info["doc_title"], page_num, current_header, current_chunk.strip()))
                    row_id = cursor.lastrowid
                    try:
                        cursor.execute("""
                            INSERT INTO manual_chunks_fts (rowid, source_file, doc_title, page_number, section_header, chunk_text)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (row_id, pdf_info["filename"], pdf_info["doc_title"], str(page_num), current_header, current_chunk.strip()))
                    except Exception:
                        pass
                    total_chunks += 1

                # Commit every 10 pages
                if page_num % 10 == 0:
                    conn.commit()
                    logger.info(f"Processed {page_num}/{num_pages} pages of {pdf_info['filename']}")

            conn.commit()
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_info['filename']}: {e}")

    cursor.execute("""
        INSERT OR REPLACE INTO system_settings (key, value, updated_at)
        VALUES ('last_sync_time', ?, CURRENT_TIMESTAMP)
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))

    conn.commit()
    conn.close()
    logger.info(f"Ingested {total_chunks} PDF chunks successfully.")
    return total_chunks


def run_full_ingestion():
    """Run initial ingestion of all Excel and PDF sources."""
    init_database()
    u_count = ingest_all_users()
    h_count = ingest_hlb_allocation()
    p_count = ingest_pdf_manuals()
    logger.info(f"Full Ingestion complete: {u_count} users, {h_count} HLB allocations, {p_count} PDF chunks.")
    return {
        "users_count": u_count,
        "hlb_allocations_count": h_count,
        "pdf_chunks_count": p_count,
        "status": "Completed"
    }

if __name__ == "__main__":
    run_full_ingestion()
