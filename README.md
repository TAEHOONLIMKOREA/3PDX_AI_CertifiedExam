# Vision AD API 테스트 GUI

FastAPI 기반 Vision Anomaly Detection API를 테스트하기 위한 GUI 애플리케이션입니다.

## 기능

### 1. 단일 이미지 추론 (`/InferenceVisionAD_Single`)
- 이미지 파일 선택 및 업로드
- 결과 이미지 실시간 표시
- Anomaly Score 표시

### 2. 배치 이미지 추론 (`/InferenceVisionAD_Batch`)
- 여러 이미지 파일 동시 선택 및 업로드
- 결과 ZIP 파일 다운로드
- overlays 폴더 + scores.csv 포함

## 설치 방법

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 애플리케이션 실행

```bash
python app.py
```

## 사용 방법

### 1. API 서버 연결
1. 상단의 "API 서버 URL" 입력란에 FastAPI 서버 주소 입력 (기본값: `http://localhost:8000`)
2. "연결" 버튼 클릭
3. 연결 상태 확인 ("연결됨" 표시)

### 2. 단일 이미지 추론
1. "단일 이미지 추론" 탭 선택
2. "이미지 선택" 버튼으로 테스트할 이미지 선택
3. "추론 실행" 버튼 클릭
4. 우측에 결과 이미지와 Anomaly Score 확인

### 3. 배치 이미지 추론
1. "배치 이미지 추론" 탭 선택
2. "이미지 선택 (여러 개)" 버튼으로 여러 이미지 선택
3. 선택된 이미지 목록 확인
4. "배치 추론 실행" 버튼 클릭
5. ZIP 파일 저장 위치 선택
6. 추론 완료 후 결과 확인

## 파일 구조

```
.
├── app.py              # 메인 GUI 애플리케이션
├── api_client.py       # FastAPI 클라이언트 모듈
├── requirements.txt    # 의존성 목록
└── README.md          # 사용 설명서
```

## 요구사항

- Python 3.8 이상
- FastAPI 서버가 실행 중이어야 합니다

## 의존성

- `requests`: HTTP 요청 처리
- `Pillow`: 이미지 처리
- `customtkinter`: 현대적인 GUI 인터페이스

## 주의사항

- FastAPI 서버가 실행되지 않으면 "서버에 연결할 수 없습니다" 오류가 발생합니다
- 대용량 배치 처리 시 시간이 소요될 수 있습니다 (timeout: 300초)
- 지원 이미지 형식: JPG, JPEG, PNG, BMP
