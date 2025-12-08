"""
Vision Anomaly Detection API 테스트 GUI 애플리케이션
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import threading
from api_client import VisionADClient
import os


class VisionADTestApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Vision AD API 테스트")
        self.root.geometry("1000x700")

        # API 클라이언트
        self.client = None

        # 이미지 참조 유지
        self.current_image = None
        self.result_image = None

        # UI 초기화
        self.setup_ui()

    def setup_ui(self):
        """UI 구성"""
        # 상단: API 서버 설정
        top_frame = ctk.CTkFrame(self.root)
        top_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(top_frame, text="API 서버 URL:", font=("Arial", 14)).pack(side="left", padx=5)
        self.url_entry = ctk.CTkEntry(top_frame, width=300, placeholder_text="http://localhost:8000")
        self.url_entry.pack(side="left", padx=5)
        self.url_entry.insert(0, "http://localhost:8000")

        ctk.CTkButton(top_frame, text="연결", command=self.connect_to_api, width=100).pack(side="left", padx=5)

        self.status_label = ctk.CTkLabel(top_frame, text="미연결", text_color="gray")
        self.status_label.pack(side="left", padx=10)

        # 탭뷰
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # 단일 이미지 탭
        self.tab_single = self.tabview.add("단일 이미지 추론")
        self.setup_single_tab()

        # 배치 이미지 탭
        self.tab_batch = self.tabview.add("배치 이미지 추론")
        self.setup_batch_tab()

        # F1 Score 계산 탭
        self.tab_f1 = self.tabview.add("F1 Score 계산")
        self.setup_f1_tab()

    def setup_single_tab(self):
        """단일 이미지 추론 탭 구성"""
        # 좌측: 입력 이미지
        left_frame = ctk.CTkFrame(self.tab_single)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(left_frame, text="입력 이미지", font=("Arial", 16, "bold")).pack(pady=5)

        self.input_image_label = ctk.CTkLabel(left_frame, text="이미지를 선택하세요", width=400, height=400)
        self.input_image_label.pack(pady=10)

        ctk.CTkButton(left_frame, text="이미지 선택", command=self.select_single_image).pack(pady=5)

        # 중앙: 버튼
        center_frame = ctk.CTkFrame(self.tab_single, width=100)
        center_frame.pack(side="left", fill="y", padx=5, pady=5)

        ctk.CTkButton(
            center_frame,
            text="→\n추론\n실행",
            command=self.run_single_inference,
            width=80,
            height=100,
            font=("Arial", 14, "bold")
        ).pack(pady=200)

        # 우측: 결과 이미지
        right_frame = ctk.CTkFrame(self.tab_single)
        right_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(right_frame, text="결과 이미지", font=("Arial", 16, "bold")).pack(pady=5)

        self.output_image_label = ctk.CTkLabel(right_frame, text="결과가 여기에 표시됩니다", width=400, height=400)
        self.output_image_label.pack(pady=10)

        self.score_label = ctk.CTkLabel(
            right_frame,
            text="Anomaly Score: -",
            font=("Arial", 18, "bold"),
            text_color="#FF6B6B"
        )
        self.score_label.pack(pady=10)

    def setup_batch_tab(self):
        """배치 이미지 추론 탭 구성"""
        # 상단: 파일 선택
        top_frame = ctk.CTkFrame(self.tab_batch)
        top_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(top_frame, text="이미지 선택 (여러 개)", command=self.select_batch_images).pack(side="left", padx=5)
        ctk.CTkButton(top_frame, text="선택 초기화", command=self.clear_batch_images).pack(side="left", padx=5)

        # 중앙: 선택된 파일 리스트
        middle_frame = ctk.CTkFrame(self.tab_batch)
        middle_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(middle_frame, text="선택된 이미지", font=("Arial", 14, "bold")).pack(pady=5)

        self.batch_listbox = ctk.CTkTextbox(middle_frame, height=300)
        self.batch_listbox.pack(fill="both", expand=True, pady=5)

        self.batch_image_paths = []

        # 하단: 실행 버튼
        bottom_frame = ctk.CTkFrame(self.tab_batch)
        bottom_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(
            bottom_frame,
            text="배치 추론 실행",
            command=self.run_batch_inference,
            height=40,
            font=("Arial", 14, "bold")
        ).pack(pady=10)

        self.batch_status_label = ctk.CTkLabel(bottom_frame, text="", font=("Arial", 12))
        self.batch_status_label.pack(pady=5)

    def setup_f1_tab(self):
        """F1 Score 계산 탭 구성"""
        # 초기화
        self.normal_image_paths = []
        self.abnormal_image_paths = []

        # 좌측: 정상 이미지
        left_frame = ctk.CTkFrame(self.tab_f1)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(left_frame, text="정상 이미지", font=("Arial", 16, "bold"), text_color="#4CAF50").pack(pady=5)

        self.normal_listbox = ctk.CTkTextbox(left_frame, height=200)
        self.normal_listbox.pack(fill="both", expand=True, pady=5)

        normal_btn_frame = ctk.CTkFrame(left_frame)
        normal_btn_frame.pack(fill="x", pady=5)

        ctk.CTkButton(normal_btn_frame, text="정상 이미지 선택", command=self.select_normal_images).pack(side="left", padx=5)
        ctk.CTkButton(normal_btn_frame, text="초기화", command=self.clear_normal_images).pack(side="left", padx=5)

        # 우측: 비정상 이미지
        right_frame = ctk.CTkFrame(self.tab_f1)
        right_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(right_frame, text="비정상 이미지", font=("Arial", 16, "bold"), text_color="#FF6B6B").pack(pady=5)

        self.abnormal_listbox = ctk.CTkTextbox(right_frame, height=200)
        self.abnormal_listbox.pack(fill="both", expand=True, pady=5)

        abnormal_btn_frame = ctk.CTkFrame(right_frame)
        abnormal_btn_frame.pack(fill="x", pady=5)

        ctk.CTkButton(abnormal_btn_frame, text="비정상 이미지 선택", command=self.select_abnormal_images).pack(side="left", padx=5)
        ctk.CTkButton(abnormal_btn_frame, text="초기화", command=self.clear_abnormal_images).pack(side="left", padx=5)

        # 하단: 설정 및 실행
        bottom_frame = ctk.CTkFrame(self.tab_f1)
        bottom_frame.pack(fill="x", padx=10, pady=10)

        # Threshold 설정
        threshold_frame = ctk.CTkFrame(bottom_frame)
        threshold_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(threshold_frame, text="Threshold:", font=("Arial", 14)).pack(side="left", padx=5)
        self.threshold_entry = ctk.CTkEntry(threshold_frame, width=100, placeholder_text="0.5")
        self.threshold_entry.pack(side="left", padx=5)
        self.threshold_entry.insert(0, "0.5")
        ctk.CTkLabel(threshold_frame, text="(Anomaly Score > Threshold → 비정상 판정)", font=("Arial", 10)).pack(side="left", padx=5)

        # 실행 버튼
        ctk.CTkButton(
            bottom_frame,
            text="F1 Score 계산 실행",
            command=self.run_f1_calculation,
            height=40,
            font=("Arial", 14, "bold")
        ).pack(pady=10)

        # 진행 상태
        self.f1_status_label = ctk.CTkLabel(bottom_frame, text="", font=("Arial", 12))
        self.f1_status_label.pack(pady=5)

        # 결과 표시
        result_frame = ctk.CTkFrame(bottom_frame)
        result_frame.pack(fill="both", expand=True, pady=10)

        ctk.CTkLabel(result_frame, text="결과", font=("Arial", 16, "bold")).pack(pady=5)

        self.f1_result_textbox = ctk.CTkTextbox(result_frame, height=200)
        self.f1_result_textbox.pack(fill="both", expand=True, pady=5)

    def connect_to_api(self):
        """API 서버 연결"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("오류", "API 서버 URL을 입력하세요")
            return

        self.client = VisionADClient(base_url=url)
        self.status_label.configure(text="연결됨", text_color="green")
        messagebox.showinfo("성공", f"{url}에 연결되었습니다")

    def select_single_image(self):
        """단일 이미지 선택"""
        file_path = filedialog.askopenfilename(
            title="이미지 선택",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        )

        if file_path:
            self.selected_image_path = file_path
            self.display_image(file_path, self.input_image_label)

    def display_image(self, image_path, label_widget, max_size=(400, 400)):
        """이미지를 라벨에 표시"""
        try:
            image = Image.open(image_path)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(image)
            label_widget.configure(image=photo, text="")
            label_widget.image = photo  # 참조 유지

        except Exception as e:
            messagebox.showerror("오류", f"이미지를 표시할 수 없습니다: {str(e)}")

    def display_pil_image(self, pil_image, label_widget, max_size=(400, 400)):
        """PIL 이미지를 라벨에 표시"""
        try:
            image = pil_image.copy()
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(image)
            label_widget.configure(image=photo, text="")
            label_widget.image = photo  # 참조 유지

        except Exception as e:
            messagebox.showerror("오류", f"이미지를 표시할 수 없습니다: {str(e)}")

    def run_single_inference(self):
        """단일 이미지 추론 실행"""
        if not self.client:
            messagebox.showerror("오류", "먼저 API 서버에 연결하세요")
            return

        if not hasattr(self, 'selected_image_path'):
            messagebox.showerror("오류", "이미지를 먼저 선택하세요")
            return

        # 비동기 처리
        def inference_task():
            self.score_label.configure(text="추론 중...")

            result_image, anomaly_score, error = self.client.inference_single(self.selected_image_path)

            if error:
                self.root.after(0, lambda: messagebox.showerror("오류", error))
                self.root.after(0, lambda: self.score_label.configure(text="Anomaly Score: -"))
            else:
                self.root.after(0, lambda: self.display_pil_image(result_image, self.output_image_label))
                self.root.after(0, lambda: self.score_label.configure(text=f"Anomaly Score: {anomaly_score:.6f}"))

        thread = threading.Thread(target=inference_task)
        thread.start()

    def select_batch_images(self):
        """배치 이미지 선택"""
        file_paths = filedialog.askopenfilenames(
            title="이미지 선택 (여러 개)",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        )

        if file_paths:
            self.batch_image_paths.extend(file_paths)
            self.update_batch_listbox()

    def clear_batch_images(self):
        """배치 이미지 선택 초기화"""
        self.batch_image_paths = []
        self.update_batch_listbox()

    def update_batch_listbox(self):
        """배치 리스트박스 업데이트"""
        self.batch_listbox.delete("1.0", "end")
        for i, path in enumerate(self.batch_image_paths, 1):
            filename = os.path.basename(path)
            self.batch_listbox.insert("end", f"{i}. {filename}\n")

    def run_batch_inference(self):
        """배치 추론 실행"""
        if not self.client:
            messagebox.showerror("오류", "먼저 API 서버에 연결하세요")
            return

        if not self.batch_image_paths:
            messagebox.showerror("오류", "이미지를 먼저 선택하세요")
            return

        # 저장 경로 선택
        output_path = filedialog.asksaveasfilename(
            title="결과 저장 위치",
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip")]
        )

        if not output_path:
            return

        # 비동기 처리
        def batch_task():
            self.batch_status_label.configure(text=f"{len(self.batch_image_paths)}개 이미지 추론 중...")

            success, error = self.client.inference_batch(self.batch_image_paths, output_path)

            if error:
                self.root.after(0, lambda: messagebox.showerror("오류", error))
                self.root.after(0, lambda: self.batch_status_label.configure(text="추론 실패"))
            else:
                self.root.after(0, lambda: messagebox.showinfo("성공", f"결과가 저장되었습니다:\n{output_path}"))
                self.root.after(0, lambda: self.batch_status_label.configure(text="추론 완료!"))

        thread = threading.Thread(target=batch_task)
        thread.start()

    def select_normal_images(self):
        """정상 이미지 선택"""
        file_paths = filedialog.askopenfilenames(
            title="정상 이미지 선택 (여러 개)",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        )

        if file_paths:
            self.normal_image_paths.extend(file_paths)
            self.update_normal_listbox()

    def select_abnormal_images(self):
        """비정상 이미지 선택"""
        file_paths = filedialog.askopenfilenames(
            title="비정상 이미지 선택 (여러 개)",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        )

        if file_paths:
            self.abnormal_image_paths.extend(file_paths)
            self.update_abnormal_listbox()

    def clear_normal_images(self):
        """정상 이미지 초기화"""
        self.normal_image_paths = []
        self.update_normal_listbox()

    def clear_abnormal_images(self):
        """비정상 이미지 초기화"""
        self.abnormal_image_paths = []
        self.update_abnormal_listbox()

    def update_normal_listbox(self):
        """정상 이미지 리스트박스 업데이트"""
        self.normal_listbox.delete("1.0", "end")
        self.normal_listbox.insert("end", f"총 {len(self.normal_image_paths)}개의 정상 이미지\n\n")
        for i, path in enumerate(self.normal_image_paths, 1):
            filename = os.path.basename(path)
            self.normal_listbox.insert("end", f"{i}. {filename}\n")

    def update_abnormal_listbox(self):
        """비정상 이미지 리스트박스 업데이트"""
        self.abnormal_listbox.delete("1.0", "end")
        self.abnormal_listbox.insert("end", f"총 {len(self.abnormal_image_paths)}개의 비정상 이미지\n\n")
        for i, path in enumerate(self.abnormal_image_paths, 1):
            filename = os.path.basename(path)
            self.abnormal_listbox.insert("end", f"{i}. {filename}\n")

    def run_f1_calculation(self):
        """F1 Score 계산 실행"""
        if not self.client:
            messagebox.showerror("오류", "먼저 API 서버에 연결하세요")
            return

        if not self.normal_image_paths:
            messagebox.showerror("오류", "정상 이미지를 먼저 선택하세요")
            return

        if not self.abnormal_image_paths:
            messagebox.showerror("오류", "비정상 이미지를 먼저 선택하세요")
            return

        # Threshold 값 가져오기
        try:
            threshold = float(self.threshold_entry.get())
            if threshold < 0 or threshold > 1:
                messagebox.showerror("오류", "Threshold 값은 0과 1 사이여야 합니다")
                return
        except ValueError:
            messagebox.showerror("오류", "올바른 Threshold 값을 입력하세요")
            return

        # 비동기 처리
        def f1_task():
            total_images = len(self.normal_image_paths) + len(self.abnormal_image_paths)
            self.f1_status_label.configure(text=f"{total_images}개 이미지 추론 중...")
            self.f1_result_textbox.delete("1.0", "end")

            result, error = self.client.calculate_f1_score(
                self.normal_image_paths,
                self.abnormal_image_paths,
                threshold
            )

            if error:
                self.root.after(0, lambda: messagebox.showerror("오류", error))
                self.root.after(0, lambda: self.f1_status_label.configure(text="계산 실패"))
            else:
                # 결과 출력
                def display_result():
                    self.f1_result_textbox.delete("1.0", "end")

                    # 통계 계산
                    normal_avg = sum(result['normal_scores'])/len(result['normal_scores'])
                    abnormal_avg = sum(result['abnormal_scores'])/len(result['abnormal_scores'])

                    output = f"""
╔═══════════════════════════════════════════════════════════════════╗
║                       🎯 F1 Score 계산 결과                       ║
╚═══════════════════════════════════════════════════════════════════╝

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  📊 데이터셋 정보                                                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
  ✓ Threshold: {result['threshold']:.4f}
  ✓ 정상 이미지: {len(result['normal_scores'])}개
  ✓ 비정상 이미지: {len(result['abnormal_scores'])}개
  ✓ 전체 이미지: {len(result['normal_scores']) + len(result['abnormal_scores'])}개


┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🎨 혼동 행렬 (Confusion Matrix)                                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

                        예측 (Predicted)
              ┌─────────────┬─────────────┐
              │  Abnormal   │   Normal    │
  ┌───────────┼─────────────┼─────────────┤
  │ Abnormal  │     {result['tp']:3d}     │     {result['fn']:3d}     │  ← 실제 비정상
실│           │     ✓TP     │     ✗FN     │
제├───────────┼─────────────┼─────────────┤
  │  Normal   │     {result['fp']:3d}     │     {result['tn']:3d}     │  ← 실제 정상
  │           │     ✗FP     │     ✓TN     │
  └───────────┴─────────────┴─────────────┘

  📌 TP (True Positive):  {result['tp']:3d}개 - 비정상을 비정상으로 올바르게 판정
  📌 TN (True Negative):  {result['tn']:3d}개 - 정상을 정상으로 올바르게 판정
  📌 FP (False Positive): {result['fp']:3d}개 - 정상을 비정상으로 잘못 판정
  📌 FN (False Negative): {result['fn']:3d}개 - 비정상을 정상으로 잘못 판정


┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  📈 성능 지표 (Performance Metrics)                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

  ╔════════════════════════════════════════════════════════════╗
  ║  🎯 F1 Score    {result['f1_score']:.4f}  ({result['f1_score']*100:6.2f}%)                     ║
  ╠════════════════════════════════════════════════════════════╣
  ║  🔍 Precision   {result['precision']:.4f}  ({result['precision']*100:6.2f}%)                     ║
  ║  📊 Recall      {result['recall']:.4f}  ({result['recall']*100:6.2f}%)                     ║
  ║  ✅ Accuracy    {result['accuracy']:.4f}  ({result['accuracy']*100:6.2f}%)                     ║
  ╚════════════════════════════════════════════════════════════╝

  💡 Precision = TP / (TP + FP) = {result['tp']} / {result['tp'] + result['fp']} = {result['precision']:.4f}
  💡 Recall    = TP / (TP + FN) = {result['tp']} / {result['tp'] + result['fn']} = {result['recall']:.4f}
  💡 Accuracy  = (TP + TN) / Total = {result['tp'] + result['tn']} / {len(result['normal_scores']) + len(result['abnormal_scores'])} = {result['accuracy']:.4f}


┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  📉 Anomaly Score 분포 분석                                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

  ✅ 정상 이미지 (Normal):
     ├─ 최소값: {min(result['normal_scores']):.6f}
     ├─ 최대값: {max(result['normal_scores']):.6f}
     ├─ 평균값: {normal_avg:.6f}
     └─ 표준편차: {(sum((x - normal_avg)**2 for x in result['normal_scores']) / len(result['normal_scores']))**0.5:.6f}

  🔴 비정상 이미지 (Abnormal):
     ├─ 최소값: {min(result['abnormal_scores']):.6f}
     ├─ 최대값: {max(result['abnormal_scores']):.6f}
     ├─ 평균값: {abnormal_avg:.6f}
     └─ 표준편차: {(sum((x - abnormal_avg)**2 for x in result['abnormal_scores']) / len(result['abnormal_scores']))**0.5:.6f}

  📊 평균 점수 차이: {abs(abnormal_avg - normal_avg):.6f}


╔═══════════════════════════════════════════════════════════════════╗
║  ✨ 계산 완료! 결과를 확인하세요.                                ║
╚═══════════════════════════════════════════════════════════════════╝
"""
                    self.f1_result_textbox.insert("1.0", output)
                    self.f1_status_label.configure(text="✅ 계산 완료!")

                self.root.after(0, display_result)

        thread = threading.Thread(target=f1_task)
        thread.start()

    def run(self):
        """애플리케이션 실행"""
        self.root.mainloop()


if __name__ == "__main__":
    app = VisionADTestApp()
    app.run()
