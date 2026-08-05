# Member Role Report — Day 9: Multi Agent A2A

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung            |
| ------------------ | -------------------- |
| Họ và tên       | Nguyễn Khánh Toàn |
| MSSV               | 2A20260184           |
| Khóa/Lớp         | K3                   |
| Vai trò chính    | System Architect & Tech Lead (SA) |
| Ngày hoàn thành | 2026-08-05           |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Thiết kế data contract giữa các agent | `core/models.py`, `core/config.py` | Schema nghiệp vụ (EC_POLICY_V1), field đặc tả trong `architecture.md` | 12 Pydantic model (`CaseInput` → `OrderContext`/`PaymentContext`/`DeliveryContext` → `PolicyDecision` → `FinalOutput`, `TraceRecord`) + hằng số cấu hình (`RC_*`, `ISSUE_*`, `MAX_*`) | Hoàn thành |
| Xây dựng orchestration engine | `agents/coordinator_agent.py`, `agents/base_agent.py`, `core/trace.py`, `core/logger.py` | `CaseInput` (1 case) | `FinalOutput` đã điều phối qua 5 agent con + `trace.jsonl` (1 dòng JSON/bước) | Hoàn thành |
| CLI entrypoint & chế độ chạy batch | `main.py` | Tham số `--mode {all,single,zip}`, `--case_id` | `output/EC_*.json`, `output.zip` (qua `DisputeService`) | Hoàn thành |

Chỉ nhận ownership cho phần bạn trực tiếp thực hiện. Liên hệ rõ phần việc của bạn với đầu vào, đầu ra và các thành viên phụ thuộc vào phần đó.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                  | Thành viên/module được hỗ trợ | Kết quả                    |
| ----------------------------- | ------------------------------------ | ---------------------------- |
| Viết `architecture.md` (sơ đồ mermaid, bảng ranh giới truy cập dữ liệu, thứ tự ưu tiên rule) | Toàn bộ nhóm (DTruong, Trường, Thi) | Mỗi thành viên biết chính xác agent mình phụ trách được đọc CSV/context nào, tránh việc PolicyAgent đọc CSV hoặc CoordinatorAgent chứa business rule khi merge code |
| Kiểm tra tích hợp end-to-end toàn pipeline | `main.py` → `DisputeService` → 6 agent | Xác nhận `python main.py --mode all` chạy hết 50 case, không có case nào crash làm sập batch |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh  |
| --------------------------- | ----------------------------- | ------------------------- | ---------------- |
| Định nghĩa toàn bộ data contract Pydantic cho pipeline | `core/models.py` | 12 class model bao phủ từ input case đến output cuối, ép kiểu và validate tự động ở ranh giới giữa các agent | `python -c "from core.models import FinalOutput; print(FinalOutput.model_fields.keys())"` |
| Xây `BaseAgent.run_with_retry` (retry + timing + tracing dùng chung) và `Tracer` | `agents/base_agent.py`, `core/trace.py` | Mọi lần agent chạy (kể cả fail) đều sinh 1 `TraceRecord` ghi vào `trace.jsonl` | `python main.py --mode all` rồi đếm dòng trong `trace.jsonl` |
| Xây `CoordinatorAgent` điều phối đúng thứ tự phụ thuộc (Order/Payment → Delivery → Policy → Verifier) và CLI `main.py` | `agents/coordinator_agent.py`, `main.py` | 50/50 case trong `input/` được xử lý, ghi ra `output/EC_*.json` và đóng gói `output.zip` | `python main.py --mode all` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Sau khi chạy `python main.py --mode all`, `trace.jsonl` có đúng 300 dòng (6 agent × 50 case), 100% `status == "SUCCESS"`, xác nhận bằng script đếm nhanh (`Counter` theo `agent`, theo `status`) — xem chi tiết ở mục 4 "Cách xác minh".

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Cần một lớp orchestration đảm bảo 5 agent domain (Order, Payment, Delivery, Policy, Verifier) chạy đúng thứ tự phụ thuộc theo `architecture.md` (Order/Payment trước, Delivery cần `OrderContext`, Policy cần cả 3 context, Verifier chạy sau cùng), đồng thời có contract dữ liệu đủ chặt để một agent không đọc nhầm field của agent khác, và mọi bước thực thi phải để lại vết (trace) phục vụ audit/debug khi 1 trong 50 case bị lỗi.

### Cách triển khai

Dùng Pydantic v2 `BaseModel` cho từng lần handoff giữa agent (`OrderContext`, `PaymentContext`, `DeliveryContext`, `PolicyDecision`, `FinalOutput`) để fail nhanh khi sai kiểu dữ liệu thay vì lỗi ngầm ở bước sau. `CoordinatorAgent.execute()` gọi tuần tự `run_with_retry()` của 5 agent con đúng theo dependency graph. `BaseAgent.run_with_retry()` là wrapper dùng chung: đo thời gian bằng `time.perf_counter()`, retry tối đa `max_retries` lần (mặc định 2) khi `execute()` raise exception, và luôn gọi `Tracer.record()` để ghi 1 dòng JSON vào `trace.jsonl` dù thành công hay thất bại. `main.py` chỉ là lớp mỏng ánh xạ 3 chế độ CLI (`all`/`single`/`zip`) sang các hàm tương ứng của `DisputeService`.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | `CaseInput` (`case_id`, `opened_at`, `customer_request.claimed_order_id`, `policy_version`) đọc từ `input/EC_*.json` |
| Output                         | `FinalOutput` đã qua `VerifierAgent`, cộng với 1 dòng `TraceRecord` trong `trace.jsonl` cho mỗi bước agent |
| Module phụ thuộc             | `OrderAgent`, `PaymentAgent`, `DeliveryAgent`, `PolicyAgent`, `VerifierAgent` (chạy bên trong `CoordinatorAgent`); `OlistCSVLoader` được khởi tạo một lần trong `DisputeService` và share cho `OrderAgent`/`PaymentAgent` để tận dụng cache |
| Module sử dụng output        | `services/dispute_service.py` (ghi `output/EC_*.json`), `services/export_service.py` (đóng gói `output.zip`) |
| Điều kiện lỗi cần xử lý | Agent con hết `max_retries` vẫn lỗi → exception được raise lên `CoordinatorAgent`, rồi lên `DisputeService.process_all_cases`, nơi mỗi case được bọc `try/except` riêng để 1 case lỗi không làm sập toàn bộ batch 50 case |

### Cách xác minh

```bash
source venv/bin/activate
python main.py --mode all
python3 -c "
import json
from collections import Counter
recs = [json.loads(l) for l in open('trace.jsonl')]
print('total records:', len(recs))
print('by agent:', Counter(r['agent'] for r in recs))
print('by status:', Counter(r['status'] for r in recs))
lat = [r['latency_ms'] for r in recs if r['agent']=='CoordinatorAgent']
print('coordinator latency avg(all)=%.2fms max=%.2fms' % (sum(lat)/len(lat), max(lat)))
print('coordinator latency avg(excl. case dau)=%.2fms' % (sum(lat[1:])/len(lat[1:])))
"
```

- **Kết quả mong đợi:** 50/50 case xử lý thành công, `output/` có 50 file JSON + `output.zip`, `trace.jsonl` có đủ bản ghi cho từng bước của từng case, latency mỗi case dưới ngưỡng mục tiêu 100ms.
- **Kết quả thực tế:** Log in ra `Processed 50 cases successfully.`; `trace.jsonl` có đúng 300 dòng (6 agent × 50 case), 100% `status == "SUCCESS"` → đạt mục tiêu "100% Trace completeness". Latency `CoordinatorAgent` trung bình 33.89ms/case tính trên cả 50 case, nhưng case đầu tiên (`EC_001`) mất 405.52ms do cold-start (lần đầu `OlistCSVLoader` đọc 3 file CSV vào pandas DataFrame và cache lại); 49 case còn lại trung bình chỉ 26.31ms/case và không case nào vượt 100ms. Mục tiêu "< 100ms/case" đạt cho toàn bộ case ngoại trừ chi phí cold-start một lần duy nhất ở case đầu batch — đây là chi phí hệ thống chấp nhận được vì chỉ xảy ra 1 lần/lần chạy `--mode all`, không lặp lại theo case.
- **Artifact/log:** `output/EC_001.json` … `output/EC_050.json`, `output.zip`, `trace.jsonl` (thư mục gốc repo).

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi 1 trong 50 case ở `input/` bị lỗi (ví dụ `claimed_order_id` không khớp hàng nào trong `data/olist_orders_dataset.csv`, khiến `OrderAgent` raise `ValueError`), cần quyết định `python main.py --mode all` nên dừng toàn bộ batch hay tiếp tục xử lý các case còn lại.
- **Các phương án đã cân nhắc:** (1) Fail-fast toàn batch — bất kỳ case nào lỗi thì dừng ngay `--mode all`, không xuất case nào cả cho tới khi sửa xong; (2) Cô lập theo case — bắt exception ở từng case trong vòng lặp, log lỗi rồi tiếp tục case tiếp theo, chỉ đóng gói `output.zip` từ các case xử lý thành công.
- **Phương án đã chọn:** (2) — cô lập theo case, hiện thực bằng `try/except` bọc quanh `process_case_file()` trong vòng `for` của `DisputeService.process_all_cases` (`services/dispute_service.py`).
- **Lý do:** Trade-off giữa reproducibility (biết chính xác case nào lỗi) và availability (không để 1 case xấu chặn 49 case tốt). Vì hệ thống chấm theo từng case độc lập (mỗi case có 1 file `output/EC_xxx.json` riêng), fail-fast sẽ khiến toàn bộ batch không có output nào chỉ vì 1 case có dữ liệu input xấu — rủi ro cao hơn nhiều so với việc log lỗi và bỏ qua case đó.
- **Bằng chứng quyết định phù hợp:** Đọc mã `services/dispute_service.py` xác nhận có `try/except Exception as e: logger.error(...)` quanh `self.process_case_file(file_path)` trong `process_all_cases`, và `package_output_zip` chỉ được gọi sau vòng lặp với danh sách `results` là các case thành công (không phụ thuộc case lỗi).

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `case_id` ghi trong `trace.jsonl` không nhất quán giữa các agent trong cùng 1 case: `CoordinatorAgent`, `OrderAgent`, `PaymentAgent`, `VerifierAgent` ghi đúng `case_id` dạng `EC_xxx`, nhưng `DeliveryAgent` và `PolicyAgent` lại ghi `order_id` gốc của Olist (chuỗi hash 32 ký tự) thay vì `case_id`.
- **Lệnh hoặc bước tái hiện:**
  ```bash
  python main.py --mode all
  python3 -c "
  import json
  recs = [json.loads(l) for l in open('trace.jsonl')]
  print(len(set(r['case_id'] for r in recs)))  # kỳ vọng 50, thực tế ra 100
  "
  ```
- **Nguyên nhân gốc:** Hàm nội bộ `_get_cid()` trong `agents/base_agent.py` (`run_with_retry`, khoảng dòng 37-47) suy luận `case_id` bằng cách: thử `hasattr(data, "case_id")`, nếu là tuple/list thì duyệt từng phần tử, cuối cùng fallback sang `hasattr(data, "order_id")`. `DeliveryAgent.execute()` nhận trực tiếp `OrderContext`, còn `PolicyAgent.execute()` nhận tuple `(OrderContext, PaymentContext, DeliveryContext)` — không model nào trong 3 model này có field `case_id` (chỉ có `order_id`), nên `_get_cid()` luôn fallback về `order_id` cho hai agent này.
- **Cách xử lý:** Chưa sửa trong phạm vi báo cáo này — đây là thay đổi contract chung (cần thêm field `case_id` vào `OrderContext`/`PaymentContext`/`DeliveryContext`, hoặc đổi chữ ký `run_with_retry` để nhận `case_id` tường minh) nên cần thống nhất với các thành viên khác trước khi sửa, tránh phá vỡ code họ đang phụ thuộc vào các model này.
- **Cách xác minh sau khi sửa:** Chưa áp dụng (chưa sửa).
- **Điều học được:** Trường dùng để audit/trace không nên suy luận gián tiếp qua nhiều loại object khác nhau bằng `hasattr`/fallback; cần truyền `case_id` tường minh xuyên suốt pipeline ngay từ đầu để đảm bảo mọi bản ghi trace của cùng 1 case đều join được với nhau.

Nếu chưa xử lý xong:

- **Phạm vi bị ảnh hưởng:** `agents/base_agent.py` (hàm `_get_cid`), gián tiếp ảnh hưởng độ tin cậy của `trace.jsonl` khi lọc theo `case_id` — cụ thể 2/6 bước mỗi case (`DeliveryAgent`, `PolicyAgent`, tức 100/300 dòng trong lần chạy vừa rồi) bị sai giá trị `case_id`.
- **Những gì đã loại trừ:** Không phải lỗi ghi file của `Tracer.record()` (hàm ghi đúng field được truyền vào); không phải lỗi ở 4 agent còn lại (`CoordinatorAgent`, `OrderAgent`, `PaymentAgent`, `VerifierAgent`) vì input của chúng có sẵn `case_id` trực tiếp hoặc là tuple có `CaseInput` ở vị trí được duyệt tới trước.
- **Bước tiếp theo:** Đề xuất thêm field `case_id: Optional[str]` vào `OrderContext`/`PaymentContext`/`DeliveryContext` khi khởi tạo ở `OrderAgent`/`PaymentAgent`, hoặc đổi `BaseAgent.run_with_retry(self, input_data, max_retries=2, case_id: Optional[str] = None)` để agent gọi tường minh thay vì dựa vào suy luận `_get_cid()`.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

Các câu hỏi mẫu (1-2) viết cho một bài lab dạng RAG/vector-index (Crossref → embedding → vector DB), không khớp trực tiếp với bài lab này (multi-agent dispute resolution trên dataset Olist tĩnh, không có bước embedding/retrieval). Tôi trả lời theo luồng thực tế của hệ thống này:

1. **Luồng dữ liệu thực tế:** `DisputeService.process_case_file()` đọc từng file `input/EC_xxx.json`, parse thành `CaseInput` (Pydantic). `CoordinatorAgent` gọi tuần tự `OrderAgent` và `PaymentAgent` (đọc `data/olist_orders_dataset.csv`, `olist_order_items_dataset.csv`, `olist_order_payments_dataset.csv` qua `OlistCSVLoader`/`OlistJoinHelper`), rồi `DeliveryAgent` (chỉ tính toán trên `OrderContext`, không đọc CSV), rồi `PolicyAgent` (áp rule `EC_POLICY_V1` theo đúng thứ tự ưu tiên trong `architecture.md`, không đọc CSV), cuối cùng `VerifierAgent` build `FinalOutput` và chạy `OutputValidator` hard-gate trước khi cho phép ghi file. `DisputeService` ghi `output/EC_xxx.json`, và với `--mode all`, `ExportService` nén toàn bộ `output/` thành `output.zip`. Mỗi bước agent (kể cả bước lỗi) sinh 1 dòng `TraceRecord` vào `trace.jsonl` qua `Tracer`.
2. **"Ground truth" trong bài lab này** không phải document ID cho retrieval, mà là 50 case cố định trong `input/` được đối chiếu với logic rule quyết định (không có nhãn đúng/sai riêng biệt lưu sẵn trong repo — hệ thống là rule-based xác định, không phải mô hình dự đoán cần eval set độc lập). "Đúng" ở đây được đo gián tiếp qua việc output có vượt qua toàn bộ `OutputValidator` hard-gate hay không, không phải so khớp với nhãn ground-truth có sẵn.
3. **Quality checks** trong bài lab này là các rule fail-fast của `OutputValidator` (giới hạn số lượng entity/evidence, khoảng confidence, cú pháp evidence ID, tính nhất quán refund–case_status) chạy **một lần** tại thời điểm `VerifierAgent` xử lý mỗi case. Repo hiện **không có** cơ chế freshness monitoring (theo dõi dữ liệu có bị cũ/lệch theo thời gian hay không) — `data/` là dataset Olist tĩnh, không có tiến trình nào chạy nền để phát hiện dữ liệu đã lỗi thời.
4. Nếu áp dụng khái niệm baseline/corrupted/repaired vào hệ thống này: phải dùng cùng 1 bộ 50 case input để đo cả 3 giai đoạn, vì nếu đổi input giữa các giai đoạn thì không thể tách bạch được sai khác trong output là do dữ liệu bị hỏng (hoặc do repair) hay chỉ đơn thuần do input khác nhau — mất tính so sánh công bằng (apples-to-apples).
5. Repair sẽ được xem là thành công khi: toàn bộ `output/EC_*.json` qua được `OutputValidator` (0 lỗi hard-gate), `trace.jsonl` có `status == "SUCCESS"` cho đủ 6 bước/case, và `output.zip` đóng gói đủ số case tương ứng với batch input — đúng các artifact/metric hiện đang dùng để xác minh pipeline trong mục 4 ở trên.

**Lưu ý:** repo hiện tại **chưa triển khai** một bộ test corrupted/repaired riêng (không có thư mục `input_corrupted/` hay file `tests/test_golden_cases.py` dù được nhắc tới trong `work_division.md`) — câu trả lời 4-5 ở trên là suy luận theo khái niệm chung của bài lab, áp vào kiến trúc thực tế của hệ thống, không phải mô tả một tính năng đã có sẵn trong code.

## 8. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Khánh Toàn
**Ngày xác nhận:** 2026-08-05
