# RocksDB-prototype

간단한 LSM-tree 기반 키-값 저장소 프로토타입입니다. 학습/시연 목적의 간이 엔진과 Flask 기반 API, Bootstrap UI, 데모/테스트 스크립트 등을 포함합니다.

**빠른 시작 (개발 환경 — 한 포트에서 실행)**

- 요구사항: Python 3.10+ 권장

1) 가상환경 생성 및 활성화

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) 의존성 설치

```bash
pip install -r requirements.txt
```

3) 한 포트에서 백엔드(및 프론트엔드 정적 파일) 실행

이 저장소의 `backend.app`는 개발 편의를 위해 `frontend/` 폴더를 정적 파일로 서빙하도록 설정되어 있습니다. 따라서 별도 정적 서버 없이 아래 명령으로 API와 UI를 한 프로세스에서 실행할 수 있습니다.

```bash
python3 -m backend.app
# 기본 주소: http://127.0.0.1:5000
```

브라우저에서 `http://127.0.0.1:5000/` 로 접속하면 UI가 표시되고, 같은 출처에서 API 호출이 작동합니다.

4) (선택) 별도 정적 서버로 프론트엔드를 띄우려면

```bash
cd frontend
python3 -m http.server 8000
# 프론트: http://127.0.0.1:8000
```

다만 이 경우 CORS 문제로 인해 API 호출이 실패할 수 있으니 `flask-cors`를 설치하거나 브라우저에서 CORS를 허용하는 방법을 사용해야 합니다. 개발 편의상 한 포트로 실행하는 방법을 권장합니다.

**구성(간단한 예)**

`backend/config.py`에 설정을 추가해 기본 호스트/포트를 바꿀 수 있습니다. 예:

```python
# backend/config.py
HOST = "0.0.0.0"
PORT = 8080
DATA_DIR = "./data"
MEMTABLE_MAX_SIZE = 100
COMPACTION_THRESHOLD = 4
```

다른 방법으로는 환경별 실행 스크립트를 만들어 필요한 값을 수정해서 사용하면 됩니다.

**주요 엔드포인트 요약**

- `POST /put` — body JSON: `{ "key": "<key>", "value": "<value>" }` (key를 생략하면 서버가 UUID 키를 생성해서 반환합니다)
- `GET /get?key=<key>` — 응답 JSON: `{ "found": true|false, "key": "<key>", "value": "<value>" }`
- `GET /stats` — 간단한 엔진 통계 (memtable 크기, SST 파일 수 등)
- `GET /keys` — 페이징 가능한 키 목록 및 최신 값: 쿼리 파라미터 `page`, `per_page`, `q`

예: API 동작 확인 (한 포트로 실행 중일 때)

```bash
curl -i -X POST 'http://127.0.0.1:5000/put' \
	-H 'Content-Type: application/json' \
	-d '{"value":"hello"}'

# 반환 예시: {"status":"ok","key":"<uuid>","value":"hello","key_generated":true}
```

**테스트 실행**

```bash
pytest -q
```

**개발/운영 주의사항**

- 저장 방식: 현 프로토타입은 SST를 간단한 텍스트 형식(`sst_{seq}.txt`)으로 저장합니다. 대용량/성능 테스트가 필요합니다.
- 위험요소: WAL(Write-Ahead Log)이 아직 완전하지 않으며, 원자적 쓰기/파일 잠금 등 동시성 보호가 미흡합니다. 운영 전 반드시 WAL/복구, 파일 잠금, 원자적 리네임 등을 구현해야 합니다.
- 보안/배포: 현재 CORS는 개발 편의상 설정되어 있을 수 있습니다. 프로덕션 전에는 CORS/호스트 바인딩을 엄격히 제한하세요.

**권장 다음 작업**

- WAL 구현 및 복구 테스트
- 파일 잠금/원자적 쓰기 구현
- API 스펙 문서화 및 입력 검증
- CI(간단한 테스트 실행) 설정

문의/기여: 저장소 소유자에게 PR 또는 이슈로 제안해 주세요.
