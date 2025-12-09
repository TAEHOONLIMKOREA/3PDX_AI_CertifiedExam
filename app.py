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
    # F1 Score 계산을 위한 Threshold 값 (고정)
    THRESHOLD = 0.68

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Vision AD API 테스트")
        self.root.geometry("1400x800")

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
        self.url_entry = ctk.CTkEntry(top_frame, width=300, placeholder_text="http://bigsoft.iptime.org:55630")
        self.url_entry.pack(side="left", padx=5)
        self.url_entry.insert(0, "http://bigsoft.iptime.org:55630")

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
        self.f1_zip_path = None  # 배치 추론 결과 ZIP 파일 경로

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

        # # Threshold 설정 (사용자 입력)
        # threshold_frame = ctk.CTkFrame(bottom_frame)
        # threshold_frame.pack(fill="x", pady=5)
        #
        # ctk.CTkLabel(threshold_frame, text="Threshold:", font=("Arial", 14)).pack(side="left", padx=5)
        # self.threshold_entry = ctk.CTkEntry(threshold_frame, width=100, placeholder_text="0.75")
        # self.threshold_entry.pack(side="left", padx=5)
        # self.threshold_entry.insert(0, "0.75")
        # ctk.CTkLabel(threshold_frame, text="(Anomaly Score > Threshold → 비정상 판정)", font=("Arial", 10)).pack(side="left", padx=5)

        # Threshold 정보 표시 (고정값)
        # threshold_label = ctk.CTkLabel(
        #     bottom_frame,
        #     text=f"Threshold: {self.THRESHOLD} (Anomaly Score > {self.THRESHOLD} → 비정상 판정)",
        #     font=("Arial", 12)
        # )
        # threshold_label.pack(pady=5)

        # 실행 버튼 프레임
        btn_frame = ctk.CTkFrame(bottom_frame)
        btn_frame.pack(fill="x", pady=10)

        # 1단계: 배치 추론 실행
        ctk.CTkButton(
            btn_frame,
            text="1 배치 추론 실행",
            command=self.run_f1_batch_inference,
            height=40,
            width=250,
            font=("Arial", 14, "bold"),
            fg_color="#2196F3"
        ).pack(side="left", padx=5, expand=True)

        # 2단계: F1 Score 계산
        ctk.CTkButton(
            btn_frame,
            text="2 F1 Score 계산",
            command=self.run_f1_score_calculation,
            height=40,
            width=250,
            font=("Arial", 14, "bold"),
            fg_color="#FF9800"
        ).pack(side="left", padx=5, expand=True)

        # 진행 상태
        self.f1_status_label = ctk.CTkLabel(bottom_frame, text="", font=("Arial", 12))
        self.f1_status_label.pack(pady=5)

        # ZIP 파일 경로 표시
        self.f1_zip_label = ctk.CTkLabel(bottom_frame, text="추론 결과 ZIP: 없음", font=("Arial", 10), text_color="gray")
        self.f1_zip_label.pack(pady=2)

        # 결과 표시 영역
        result_main_frame = ctk.CTkScrollableFrame(bottom_frame, width=500, height=800)
        result_main_frame.pack(fill="both", expand=True, pady=10)

        # 결과 타이틀
        title_frame = ctk.CTkFrame(result_main_frame)
        title_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(title_frame, text="🎯 F1 Score 계산 결과", font=("Arial", 18, "bold")).pack(pady=10)

        # 1. 데이터셋 정보
        info_frame = ctk.CTkFrame(result_main_frame)
        info_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(info_frame, text="📊 데이터셋 정보", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=5)
        self.f1_info_label = ctk.CTkLabel(info_frame, text="", font=("Arial", 12), justify="left")
        self.f1_info_label.pack(anchor="w", padx=20, pady=5)

        # 2. Confusion Matrix (2x2 표)
        cm_frame = ctk.CTkFrame(result_main_frame)
        cm_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(cm_frame, text="🎨 Confusion Matrix", font=("Arial", 14, "bold")).pack(pady=5)

        # 표 컨테이너
        table_container = ctk.CTkFrame(cm_frame)
        table_container.pack(pady=5)

        # 헤더 행
        header_frame = ctk.CTkFrame(table_container, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=4, sticky="ew")
        ctk.CTkLabel(header_frame, text="예측 (Predicted)", font=("Arial", 12, "bold")).pack()

        # 열 헤더
        ctk.CTkLabel(table_container, text="", width=70).grid(row=1, column=0)
        ctk.CTkLabel(table_container, text="", width=40).grid(row=1, column=1)
        ctk.CTkLabel(table_container, text="Abnormal", font=("Arial", 11, "bold"), width=130).grid(row=1, column=2, padx=2, pady=2)
        ctk.CTkLabel(table_container, text="Normal", font=("Arial", 11, "bold"), width=130).grid(row=1, column=3, padx=2, pady=2)

        # 실제 (세로) 레이블
        actual_label_frame = ctk.CTkFrame(table_container, fg_color="transparent")
        actual_label_frame.grid(row=2, column=0, rowspan=2, sticky="ns")
        ctk.CTkLabel(actual_label_frame, text="실제\n(Actual)", font=("Arial", 10, "bold"), justify="center").pack(expand=True)

        # 행 헤더
        ctk.CTkLabel(table_container, text="Abnormal", font=("Arial", 10, "bold"), width=85).grid(row=2, column=1, padx=2, pady=2)
        ctk.CTkLabel(table_container, text="Normal", font=("Arial", 10, "bold"), width=85).grid(row=3, column=1, padx=2, pady=2)

        # 셀 (TP, FN, FP, TN)
        self.cm_tp_label = ctk.CTkLabel(table_container, text="TP\n-", font=("Arial", 15, "bold"),
                                        width=130, height=65, fg_color="#4CAF50", corner_radius=5)
        self.cm_tp_label.grid(row=2, column=2, padx=2, pady=2)

        self.cm_fn_label = ctk.CTkLabel(table_container, text="FN\n-", font=("Arial", 15, "bold"),
                                        width=130, height=65, fg_color="#FF6B6B", corner_radius=5)
        self.cm_fn_label.grid(row=2, column=3, padx=2, pady=2)

        self.cm_fp_label = ctk.CTkLabel(table_container, text="FP\n-", font=("Arial", 15, "bold"),
                                        width=130, height=65, fg_color="#FF6B6B", corner_radius=5)
        self.cm_fp_label.grid(row=3, column=2, padx=2, pady=2)

        self.cm_tn_label = ctk.CTkLabel(table_container, text="TN\n-", font=("Arial", 15, "bold"),
                                        width=130, height=65, fg_color="#4CAF50", corner_radius=5)
        self.cm_tn_label.grid(row=3, column=3, padx=2, pady=2)

        # Confusion Matrix 설명
        self.cm_desc_label = ctk.CTkLabel(cm_frame, text="", font=("Arial", 10), justify="left")
        self.cm_desc_label.pack(anchor="w", padx=20, pady=5)

        # 3. 성능 지표
        metrics_frame = ctk.CTkFrame(result_main_frame)
        metrics_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(metrics_frame, text="📈 성능 지표 (Performance Metrics)", font=("Arial", 14, "bold")).pack(pady=5)

        # 지표 그리드
        metrics_grid = ctk.CTkFrame(metrics_frame)
        metrics_grid.pack(pady=5)

        self.f1_score_label = ctk.CTkLabel(metrics_grid, text="F1 Score: -", font=("Arial", 16, "bold"),
                                          width=220, height=55, fg_color="#FF9800", corner_radius=5)
        self.f1_score_label.grid(row=0, column=0, columnspan=2, padx=4, pady=4)

        self.precision_label = ctk.CTkLabel(metrics_grid, text="Precision: -", font=("Arial", 13),
                                           width=220, height=45, fg_color="#2196F3", corner_radius=5)
        self.precision_label.grid(row=1, column=0, padx=4, pady=4)

        self.recall_label = ctk.CTkLabel(metrics_grid, text="Recall: -", font=("Arial", 13),
                                        width=220, height=45, fg_color="#2196F3", corner_radius=5)
        self.recall_label.grid(row=1, column=1, padx=4, pady=4)

        self.accuracy_label = ctk.CTkLabel(metrics_grid, text="Accuracy: -", font=("Arial", 13),
                                          width=448, height=45, fg_color="#9C27B0", corner_radius=5)
        self.accuracy_label.grid(row=2, column=0, columnspan=2, padx=4, pady=4)

        # 4. Anomaly Score 분포
        dist_frame = ctk.CTkFrame(result_main_frame)
        dist_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(dist_frame, text="📉 Anomaly Score 분포 분석", font=("Arial", 14, "bold")).pack(pady=5)
        self.f1_dist_label = ctk.CTkLabel(dist_frame, text="", font=("Arial", 11), justify="left")
        self.f1_dist_label.pack(anchor="w", padx=20, pady=5)

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

    def run_f1_batch_inference(self):
        """F1 Score용 배치 추론 실행 (1단계)"""
        if not self.client:
            messagebox.showerror("오류", "먼저 API 서버에 연결하세요")
            return

        if not self.normal_image_paths:
            messagebox.showerror("오류", "정상 이미지를 먼저 선택하세요")
            return

        if not self.abnormal_image_paths:
            messagebox.showerror("오류", "비정상 이미지를 먼저 선택하세요")
            return

        # 저장 경로 선택
        output_path = filedialog.asksaveasfilename(
            title="배치 추론 결과 저장 위치",
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip")]
        )

        if not output_path:
            return

        # 모든 이미지 합치기
        all_images = self.normal_image_paths + self.abnormal_image_paths

        # 비동기 처리
        def batch_task():
            try:
                total_images = len(all_images)
                self.f1_status_label.configure(text=f"1단계: {total_images}개 이미지 배치 추론 중...")

                success, error = self.client.inference_batch(all_images, output_path)

                if error:
                    print(f"ERROR: {error}")
                    self.root.after(0, lambda: messagebox.showerror("오류", error))
                    self.root.after(0, lambda: self.f1_status_label.configure(text="❌ 배치 추론 실패"))
                else:
                    # 성공 시 ZIP 경로 저장
                    self.f1_zip_path = output_path
                    self.root.after(0, lambda: messagebox.showinfo("성공", f"배치 추론 완료!\n결과 저장: {output_path}"))
                    self.root.after(0, lambda: self.f1_status_label.configure(text="✅ 배치 추론 완료! (2단계: F1 Score 계산 버튼을 눌러주세요)"))
                    self.root.after(0, lambda: self.f1_zip_label.configure(text=f"추론 결과 ZIP: {os.path.basename(output_path)}", text_color="green"))

            except Exception as e:
                import traceback
                error_msg = traceback.format_exc()
                print(f"EXCEPTION in batch_task:\n{error_msg}")
                self.root.after(0, lambda: messagebox.showerror("예외 발생", f"예상치 못한 오류:\n{str(e)}"))
                self.root.after(0, lambda: self.f1_status_label.configure(text="❌ 예외 발생"))

        thread = threading.Thread(target=batch_task)
        thread.start()

    def run_f1_score_calculation(self):
        """저장된 ZIP에서 F1 Score 계산 (2단계)"""
        if not self.client:
            messagebox.showerror("오류", "먼저 API 서버에 연결하세요")
            return

        if not self.f1_zip_path or not os.path.exists(self.f1_zip_path):
            messagebox.showerror("오류", "먼저 1단계 '배치 추론 실행'을 완료하세요")
            return

        if not self.normal_image_paths or not self.abnormal_image_paths:
            messagebox.showerror("오류", "정상/비정상 이미지를 선택하세요")
            return

        # 비동기 처리
        def f1_task():
            try:
                self.f1_status_label.configure(text="2단계: F1 Score 계산 중...")

                result, error = self.client.calculate_f1_from_zip(
                    self.f1_zip_path,
                    self.normal_image_paths,
                    self.abnormal_image_paths,
                    self.THRESHOLD  # 고정된 Threshold 값 사용
                )

                if error:
                    print(f"ERROR: {error}")
                    self.root.after(0, lambda: messagebox.showerror("오류", error))
                    self.root.after(0, lambda: self.f1_status_label.configure(text="❌ F1 Score 계산 실패"))
                else:
                    # 결과 출력
                    def display_result():
                        # 통계 계산
                        normal_avg = sum(result['normal_scores'])/len(result['normal_scores'])
                        abnormal_avg = sum(result['abnormal_scores'])/len(result['abnormal_scores'])
                        normal_std = (sum((x - normal_avg)**2 for x in result['normal_scores']) / len(result['normal_scores']))**0.5
                        abnormal_std = (sum((x - abnormal_avg)**2 for x in result['abnormal_scores']) / len(result['abnormal_scores']))**0.5

                        # 1. 데이터셋 정보 업데이트
                        info_text = f"""✓ 정상 이미지: {len(result['normal_scores'])}개
                                        ✓ 비정상 이미지: {len(result['abnormal_scores'])}개
                                        ✓ 전체 이미지: {len(result['normal_scores']) + len(result['abnormal_scores'])}개"""
                        self.f1_info_label.configure(text=info_text)

                        # 2. Confusion Matrix 업데이트
                        self.cm_tp_label.configure(text=f"TP\n{result['tp']}")
                        self.cm_fn_label.configure(text=f"FN\n{result['fn']}")
                        self.cm_fp_label.configure(text=f"FP\n{result['fp']}")
                        self.cm_tn_label.configure(text=f"TN\n{result['tn']}")

                        cm_desc_text = f"""TP (True Positive):  {result['tp']:3d}개 - 비정상을 비정상으로 올바르게 판정
                                        TN (True Negative):  {result['tn']:3d}개 - 정상을 정상으로 올바르게 판정
                                        FP (False Positive): {result['fp']:3d}개 - 정상을 비정상으로 잘못 판정
                                        FN (False Negative): {result['fn']:3d}개 - 비정상을 정상으로 잘못 판정"""
                        self.cm_desc_label.configure(text=cm_desc_text)

                        # 3. 성능 지표 업데이트
                        self.f1_score_label.configure(text=f"F1 Score: {result['f1_score']:.4f} ({result['f1_score']*100:.2f}%)")
                        self.precision_label.configure(text=f"Precision: {result['precision']:.4f} ({result['precision']*100:.2f}%)")
                        self.recall_label.configure(text=f"Recall: {result['recall']:.4f} ({result['recall']*100:.2f}%)")
                        self.accuracy_label.configure(text=f"Accuracy: {result['accuracy']:.4f} ({result['accuracy']*100:.2f}%)")

                        # 4. Anomaly Score 분포 업데이트
                        dist_text = f"""✅ 정상 이미지 (Normal):
   • 최소값: {min(result['normal_scores']):.6f}
   • 최대값: {max(result['normal_scores']):.6f}
   • 평균값: {normal_avg:.6f}
   • 표준편차: {normal_std:.6f}

🔴 비정상 이미지 (Abnormal):
   • 최소값: {min(result['abnormal_scores']):.6f}
   • 최대값: {max(result['abnormal_scores']):.6f}
   • 평균값: {abnormal_avg:.6f}
   • 표준편차: {abnormal_std:.6f}

📊 평균 점수 차이: {abs(abnormal_avg - normal_avg):.6f}"""
                        self.f1_dist_label.configure(text=dist_text)

                        self.f1_status_label.configure(text="✅ F1 Score 계산 완료!")

                    self.root.after(0, display_result)

            except Exception as e:
                import traceback
                error_msg = traceback.format_exc()
                print(f"EXCEPTION in f1_task:\n{error_msg}")
                self.root.after(0, lambda: messagebox.showerror("예외 발생", f"예상치 못한 오류:\n{str(e)}"))
                self.root.after(0, lambda: self.f1_status_label.configure(text="❌ 예외 발생"))

        thread = threading.Thread(target=f1_task)
        thread.start()

    def run(self):
        """애플리케이션 실행"""
        self.root.mainloop()


if __name__ == "__main__":
    app = VisionADTestApp()
    app.run()
