import re
import os
import json
import requests
import time


def current_date():
    from datetime import datetime

    return datetime.now().strftime("%Y%m%d")


def fetch_arxiv_papers(term):
    # train dataset domain: cs.AI
    # test dataset domain: 1. q-bio.SC, 2. cond-mat.mes-hall, 3. hep-ex
    # url = f"http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+all:{term[0]}+OR+all:{term[1]}+OR+all:{term[2]}+submittedDate:[20060101+TO+20240721]&start=0&max_results=10&sortBy=relevance&sortOrder=descending"
    # url = f"http://export.arxiv.org/api/query?search_query=cat:hep-ex+OR+all:{term[0]}+OR+all:{term[1]}+OR+all:{term[2]}+submittedDate:[20060101+TO+20240721]&start=0&max_results=10&sortBy=relevance&sortOrder=descending"
    url = f"http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+all:{term}+submittedDate:[20060101+TO+20240721]&start=0&max_results=10&sortBy=relevance&sortOrder=descending"
    response = requests.get(url)
    response_text = response.text
    return response_text


def parse_arxiv_response(response_text):
    import xml.etree.ElementTree as ET

    root = ET.fromstring(response_text)
    papers = []
    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        title = entry.find("{http://www.w3.org/2005/Atom}title").text
        summary = entry.find("{http://www.w3.org/2005/Atom}summary").text
        namespaces = {
            "arxiv": "http://arxiv.org/schemas/atom",
            "atom": "http://www.w3.org/2005/Atom",
            "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
        }

        primary_category = root.find(".//arxiv:primary_category", namespaces)
        term_value = (
            primary_category.get("term") if primary_category is not None else None
        )
        paper_info = {
            "title": title,
            "summary": summary,
            "term": term_value,
        }
        papers.append(paper_info)
    return papers


def process_translation_terms_data(turn_index, paper_index, data, terms):
    response_text = fetch_arxiv_papers(", ".join(terms))
    summaries = parse_arxiv_response(response_text)

    entries = data.split("\n\n")  # Split data into separate entries

    processed_data = {}
    processed_data["terms"] = terms

    # Select the details of the paper
    if summaries[paper_index]["term"] == None:
        processed_data["domain"] = "None"
    else:
        processed_data["domain"] = summaries[paper_index]["term"]
    processed_data["paper"] = summaries[paper_index]["title"]
    processed_data["summary"] = summaries[paper_index]["summary"]

    entry_data = {}
    for i, entry in enumerate(entries, 1):
        current_entry = {
            "terms": [],
            "english": "",
            "korean": "",
            "score": 0,
            "parentheses_count": 0,
            "suggestions": "",
        }
        for line in entry.strip().split("\n"):
            line = line.strip()
            if line.startswith("english:"):
                current_entry["english"] = line[len("english:") :].strip()
            elif line.startswith("korean:"):
                current_entry["korean"] = line[len("korean:") :].strip()
            elif line.startswith("score:"):
                current_entry["score"] = int(
                    line[len("score:") :].strip().split("/")[0]
                )
            elif line.startswith("parentheses_count:"):
                current_entry["parentheses_count"] = int(
                    line[len("parentheses_count:") :].strip()
                )
            elif line.startswith("suggestions:"):
                current_entry["suggestions"] = line[len("suggestions:") :].strip()

        for term in terms:
            if term.lower() in current_entry["english"].lower():
                current_entry["terms"].append(term)

        entry_data[f"{i}"] = current_entry

    results = {
        "turn_index": turn_index,
        "terms": processed_data["terms"],
        "domain": processed_data["domain"],
        "paper": processed_data["paper"],
        "summary": processed_data["summary"],
        **entry_data,
    }

    return results


def process_translation_term_data(turn_index, paper_index, summaries, data, term):
    processed_data = {
        "term": term,
        "domain": (
            summaries[paper_index]["term"] if summaries[paper_index]["term"] else "None"
        ),
        "paper": (
            summaries[paper_index]["title"]
            if summaries[paper_index]["title"]
            else "None"
        ),
        "summary": (
            summaries[paper_index]["summary"]
            if summaries[paper_index]["summary"]
            else "None"
        ),
    }

    entry_data = {}
    for line in data.strip().split("\n"):
        line = line.strip()
        if line.startswith("english:"):
            entry_data["english"] = line[len("english:") :].strip()
        elif line.startswith("korean:"):
            entry_data["korean"] = line[len("korean:") :].strip()
        elif line.startswith("score:"):
            entry_data["score"] = int(line[len("score:") :].strip().split("/")[0])
        elif line.startswith("parentheses_count:"):
            entry_data["parentheses_count"] = int(
                line[len("parentheses_count:") :].strip()
            )
        elif line.startswith("suggestions:"):
            entry_data["suggestions"] = line[len("suggestions:") :].strip()

    results = {
        "turn_index": turn_index,
        "term": processed_data["term"],
        "domain": processed_data["domain"],
        "paper": processed_data["paper"],
        "summary": processed_data["summary"],
        **entry_data,
    }

    return results


def process_translation_term_data_arxiv(
    turn_index, paper_index, arxiv_entry, data, term
):
    processed_data = {
        "term": term,
        "domain": (arxiv_entry["term"] if arxiv_entry["term"] else "None"),
        "paper": (
            arxiv_entry["response"][paper_index]["title"]
            if arxiv_entry["response"][paper_index]["title"]
            else "None"
        ),
        "summary": (
            arxiv_entry["response"][paper_index]["summary"]
            if arxiv_entry["response"][paper_index]["summary"]
            else "None"
        ),
    }

    entry_data = {}
    for line in data.strip().split("\n"):
        line = line.strip()
        if line.startswith("english:"):
            entry_data["english"] = line[len("english:") :].strip()
        elif line.startswith("korean:"):
            entry_data["korean"] = line[len("korean:") :].strip()
        elif line.startswith("score:"):
            entry_data["score"] = int(line[len("score:") :].strip().split("/")[0])
        elif line.startswith("parentheses_count:"):
            entry_data["parentheses_count"] = int(
                line[len("parentheses_count:") :].strip()
            )
        elif line.startswith("suggestions:"):
            entry_data["suggestions"] = line[len("suggestions:") :].strip()

    results = {
        "turn_index": turn_index,
        "term": processed_data["term"],
        "domain": processed_data["domain"],
        "paper": processed_data["paper"],
        "summary": processed_data["summary"],
        **entry_data,
    }

    return results


def load_json_file(file_path):
    # Load data from JSON file
    with open(file_path, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)

    return data


def save_json_file(
    train_data, directory_name="dataset_term", file_name="dataset_turn1.json"
):
    # Create directory path
    directory_path = os.path.join(os.getcwd(), directory_name)

    # Create directory if it doesn't exist
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"'{directory_name}' 디렉토리가 생성되었습니다.")
    else:
        print(f"'{directory_name}' 디렉토리가 이미 존재합니다.")

    # Create file path
    file_path = os.path.join(directory_path, file_name)

    # Save data as JSON file
    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(train_data, json_file, ensure_ascii=False, indent=4)

    print(f"데이터가 {file_path}에 저장되었습니다.")
