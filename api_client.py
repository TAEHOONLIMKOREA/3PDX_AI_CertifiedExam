"""
FastAPI 이상 탐지 API 클라이언트
"""
import requests
from typing import Tuple, List, Optional, Dict
from PIL import Image
import io
import os
import zipfile
import csv
import tempfile


class VisionADClient:
    """Vision Anomaly Detection API 클라이언트"""

    def __init__(self, base_url: str = "http://bigsoft.iptime.org:55630"):
        """
        Args:
            base_url: FastAPI 서버 주소
        """
        self.base_url = base_url.rstrip('/')

    def inference_single(self, image_path: str) -> Tuple[Optional[Image.Image], Optional[float], Optional[str]]:
        """
        단일 이미지 이상 탐지 추론

        Args:
            image_path: 이미지 파일 경로

        Returns:
            (결과 이미지, anomaly_score, 에러 메시지)
        """
        try:
            url = f"{self.base_url}/InferenceVisionAD_Single"

            with open(image_path, 'rb') as f:
                files = {'file': (image_path.split('/')[-1], f, 'image/jpeg')}
                response = requests.post(url, files=files, timeout=60)

            if response.status_code == 200:
                # 헤더에서 anomaly score 추출
                anomaly_score = float(response.headers.get('X-Anomaly-Score', 0.0))

                # 이미지 데이터를 PIL Image로 변환
                result_image = Image.open(io.BytesIO(response.content))

                return result_image, anomaly_score, None
            else:
                return None, None, f"API Error: {response.status_code}"

        except requests.exceptions.ConnectionError:
            return None, None, "서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요."
        except requests.exceptions.Timeout:
            return None, None, "요청 시간이 초과되었습니다."
        except Exception as e:
            return None, None, f"Error: {str(e)}"

    def inference_batch(self, image_paths: List[str], output_path: str) -> Tuple[bool, Optional[str]]:
        """
        배치 이미지 이상 탐지 추론

        Args:
            image_paths: 이미지 파일 경로 리스트
            output_path: 결과 ZIP 파일을 저장할 경로

        Returns:
            (성공 여부, 에러 메시지)
        """
        try:
            url = f"{self.base_url}/InferenceVisionAD_Batch"

            files = []
            for img_path in image_paths:
                with open(img_path, 'rb') as f:
                    file_content = f.read()
                    filename = img_path.split('\\')[-1].split('/')[-1]
                    files.append(('files', (filename, io.BytesIO(file_content), 'image/jpeg')))

            response = requests.post(url, files=files, timeout=300)

            if response.status_code == 200:
                # ZIP 파일로 저장
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True, None
            else:
                return False, f"API Error: {response.status_code}"

        except requests.exceptions.ConnectionError:
            return False, "서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요."
        except requests.exceptions.Timeout:
            return False, "요청 시간이 초과되었습니다."
        except Exception as e:
            return False, f"Error: {str(e)}"

    def calculate_f1_score(self, normal_images: List[str], abnormal_images: List[str],
                          threshold: float = 0.5) -> Tuple[Optional[Dict], Optional[str]]:
        """
        정상/비정상 이미지를 배치 추론하여 F1 Score 계산 (inference_batch 사용)

        Args:
            normal_images: 정상 이미지 경로 리스트
            abnormal_images: 비정상 이미지 경로 리스트
            threshold: 이상 판정 임계값 (anomaly_score > threshold이면 비정상)

        Returns:
            (결과 딕셔너리, 에러 메시지)
            결과 딕셔너리 구조:
            {
                'threshold': float,
                'normal_scores': List[float],
                'abnormal_scores': List[float],
                'tp': int, 'fp': int, 'tn': int, 'fn': int,
                'precision': float, 'recall': float, 'f1_score': float,
                'accuracy': float
            }
        """
        temp_zip_path = None

        try:
            # 모든 이미지를 하나의 리스트로 합치기
            all_images = normal_images + abnormal_images

            if not all_images:
                return None, "이미지가 하나도 선택되지 않았습니다"

            # 임시 ZIP 파일 생성
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.zip', delete=False) as temp_zip:
                temp_zip_path = temp_zip.name

            # 배치 추론 실행
            success, error = self.inference_batch(all_images, temp_zip_path)

            if not success:
                return None, error

            # ZIP 파일에서 scores.csv 추출 및 파싱
            score_dict = {}  # {filename: anomaly_score}

            try:
                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                    # ZIP 내용 확인
                    zip_contents = zip_ref.namelist()
                    print(f"DEBUG: ZIP 파일 내용: {zip_contents}")

                    # scores.csv 읽기
                    if 'scores.csv' not in zip_contents:
                        return None, f"결과 ZIP에 scores.csv가 없습니다. 포함된 파일: {zip_contents}"

                    with zip_ref.open('scores.csv') as csv_file:
                        # CSV 파싱
                        csv_content = csv_file.read().decode('utf-8')
                        print(f"DEBUG: CSV 내용 미리보기:\n{csv_content[:500]}")

                        csv_reader = csv.DictReader(csv_content.splitlines())

                        # CSV 헤더 확인
                        fieldnames = csv_reader.fieldnames
                        print(f"DEBUG: CSV 컬럼: {fieldnames}")

                        for row in csv_reader:
                            # CSV 구조: img_path, anomaly_score 등
                            img_path_full = (row.get('img_path') or
                                           row.get('filename') or
                                           row.get('image') or
                                           row.get('file_name') or
                                           row.get('image_name') or '')

                            score_str = (row.get('anomaly_score') or
                                       row.get('score') or
                                       row.get('anomaly') or '0')

                            if not img_path_full:
                                print(f"DEBUG: 파일 경로를 찾을 수 없는 행: {row}")
                                continue

                            # 전체 경로에서 파일명만 추출
                            filename = os.path.basename(img_path_full)

                            try:
                                score = float(score_str)
                            except ValueError:
                                print(f"DEBUG: 점수 변환 실패: {score_str}")
                                score = 0.0

                            score_dict[filename] = score
                            print(f"DEBUG: 파일명={filename}, 점수={score}")

                print(f"DEBUG: 추출된 점수 딕셔너리: {score_dict}")

            except Exception as e:
                return None, f"ZIP/CSV 파싱 오류: {str(e)}"

            # 정상/비정상 이미지의 점수 분리
            normal_scores = []
            abnormal_scores = []

            for img_path in normal_images:
                filename = os.path.basename(img_path)
                if filename in score_dict:
                    normal_scores.append(score_dict[filename])
                else:
                    return None, f"정상 이미지 '{filename}'의 점수를 찾을 수 없습니다"

            for img_path in abnormal_images:
                filename = os.path.basename(img_path)
                if filename in score_dict:
                    abnormal_scores.append(score_dict[filename])
                else:
                    return None, f"비정상 이미지 '{filename}'의 점수를 찾을 수 없습니다"

            # 혼동 행렬 계산
            # TN: 정상 이미지를 정상으로 판정 (score <= threshold)
            tn = sum(1 for score in normal_scores if score <= threshold)
            # FP: 정상 이미지를 비정상으로 판정 (score > threshold)
            fp = sum(1 for score in normal_scores if score > threshold)
            # TP: 비정상 이미지를 비정상으로 판정 (score > threshold)
            tp = sum(1 for score in abnormal_scores if score > threshold)
            # FN: 비정상 이미지를 정상으로 판정 (score <= threshold)
            fn = sum(1 for score in abnormal_scores if score <= threshold)

            # 성능 지표 계산
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0

            result = {
                'threshold': threshold,
                'normal_scores': normal_scores,
                'abnormal_scores': abnormal_scores,
                'tp': tp,
                'fp': fp,
                'tn': tn,
                'fn': fn,
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score,
                'accuracy': accuracy
            }

            return result, None

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"ERROR: F1 Score 계산 중 예외 발생:\n{error_detail}")
            return None, f"F1 Score 계산 오류: {str(e)}\n\n상세 정보:\n{error_detail}"

        finally:
            # 임시 ZIP 파일 삭제
            if temp_zip_path and os.path.exists(temp_zip_path):
                try:
                    os.remove(temp_zip_path)
                except:
                    pass  # 삭제 실패해도 무시
