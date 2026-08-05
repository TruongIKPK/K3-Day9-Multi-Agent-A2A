# Member Role Report — Day 9: Multi Agent A2A

## 1. Thông tin cá nhân

| Thông tin       | Nội dung |
| --------------- | ------------ |
| Họ và tên       | Lê Nguyễn Phi Trường |
| MSSV            | 2A20261541 |
| Khóa/Lớp        | K3 |
| Vai trò chính   | Business Policy Lead & Rules Engine Engineer |
| Ngày hoàn thành | 2026-08-05 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **Policy Rules Engine** | `agents/policy_agent.py`<br>`prompts/policy_prompts.py` | `(OrderContext, PaymentContext, DeliveryContext)` | `PolicyDecision` object | Hoàn thành |
| **Evidence Builder** | `utils/evidence.py` | Raw entity IDs từ các domain context | Sanitized & Deduplicated `evidence_ids` | Hoàn thành |
| **Financial Money Engine** | `utils/money.py` | Float price & freight values | Rounded BRL values & split tolerance boolean | Hoàn thành |
| **Policy Test Suite** | `tests/test_policy_agent.py`<br>`tests/test_evidence.py` | Mock context tuples | Unit test pass/fail results | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| :--- | :--- | :--- |
| Định nghĩa quy tắc kiểm tra khớp tiền tệ | Thi (`agents/verifier_agent.py`) | Giúp Verifier Agent bắt đúng lỗi khi refund > 0 trong trạng thái `no_action` |
| Kiểm thử dữ liệu mốc thời gian | DTruong (`agents/delivery_agent.py`) | Xác minh logic so sánh mốc `delivered_carrier_date` vs `shipping_limit_date` |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Cài đặt 6 quy tắc `EC_POLICY_V1` | `agents/policy_agent.py:execute` | `PolicyDecision` chuẩn xác 100% cho 50 case | `pytest tests/test_policy_agent.py` |
| Xử lý tiền tệ BRL & Split Payment | `utils/money.py:is_within_split_tolerance` | Tính toán chính xác sai số $\le 0.10$ BRL | `pytest tests/test_policy_agent.py` |
| Sinh Evidence ID chuẩn cú pháp | `utils/evidence.py:build_*` | Danh sách `evidence_ids` đúng cú pháp $100\%$ | `pytest tests/test_evidence.py` |

**Output cụ thể tạo ra:**
Module `PolicyAgent` phân loại chính xác $100\%$ primary issue cho 50 case (bao gồm `canceled_order_paid`, `unavailable_order_paid`, `late_delivery_seller`, `late_delivery_logistics`, `valid_split_payment`, `unsupported_late_claim`), tính tiền hoàn BRL không bị lỗi làm tròn và trả về bằng chứng `policy:<root_cause_code>` hợp lệ.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Trong bài toán xử lý tranh chấp thương mại điện tử Olist, khiếu nại của khách hàng không thể giải quyết bằng cảm tính. Hệ thống phải đối chiếu dữ liệu từ 3 domain (Order, Payment, Delivery) để xác định:
1. Vấn đề chính (`primary_issue`).
2. Trạng thái xử lý (`case_status`: `action_required` hay `no_action`).
3. Bên chịu trách nhiệm (`responsible_party`: `platform`, `seller`, hay `logistics_provider`).
4. Khoản hoàn tiền đề xuất (`recommended_refund_brl`).
5. Bằng chứng chính sách (`policy:<root_cause_code>`).

### Cách triển khai
Tôi xây dựng một **Cây ưu tiên quyết định (Priority Decision Tree)** dựa trên đúng thứ tự của đề bài:

```python
# Thuật toán đánh giá ưu tiên luật trong PolicyAgent
1. IF order_status == "canceled" AND payment_total > 0:
   => primary_issue = "canceled_order_paid", refund = payment_total, party = platform
2. ELIF order_status == "unavailable" AND payment_total > 0:
   => primary_issue = "unavailable_order_paid", refund = payment_total, party = platform
3. ELIF delivered_customer_date > estimated_delivery_date:
   IF delivered_carrier_date > shipping_limit_date:
      => primary_issue = "late_delivery_seller", refund = freight_total, party = seller
   ELSE:
      => primary_issue = "late_delivery_logistics", refund = freight_total, party = logistics_provider
4. ELIF is_split_payment AND abs(payment_total - (item_total + freight_total)) <= 0.10:
   => primary_issue = "valid_split_payment", refund = 0.0, party = None
5. ELSE:
   => primary_issue = "unsupported_late_claim", refund = 0.0, party = None
```

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input** | `Tuple[OrderContext, PaymentContext, DeliveryContext]` |
| **Output** | `PolicyDecision(primary_issue, case_status, confidence, cause_code, responsible_party_type, responsible_party_id, recommended_refund_brl, resolution_actions, policy_evidence_id)` |
| **Module phụ thuộc** | Dữ liệu từ `OrderAgent`, `PaymentAgent`, `DeliveryAgent` (do DTruong phát triển) |
| **Module sử dụng output** | `VerifierAgent` (do Thi phát triển) và `CoordinatorAgent` |
| **Điều kiện lỗi cần xử lý** | Đơn hàng không có item (full refund payment total), thiếu mốc thời gian giao hàng |

### Cách xác minh

```bash
pytest tests/test_policy_agent.py tests/test_evidence.py
```

- **Kết quả mong đợi:** Tất cả các test cases kiểm tra quy tắc policy, tiền hoàn và format evidence ID đều trả về `PASSED`.
- **Kết quả thực tế:** 100% unit tests pass không có lỗi.
- **Artifact/log:** `tests/test_policy_agent.py`.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần lựa chọn phương án đánh giá chính sách cho Policy Agent trong cuộc thi AI Competition.
- **Các phương án đã cân nhắc:**
  1. *Phương án A (Pure LLM Prompting)*: Đưa toàn bộ context vào Prompt và yêu cầu LLM tự suy luận ra `primary_issue` và `recommended_refund_brl`.
  2. *Phương án B (Deterministic Python Rules Engine - Lựa chọn)*: Xây dựng bộ quy tắc Python thuần tính toán chính xác 100% dựa trên bảng luật `EC_POLICY_V1`, LLM chỉ hỗ trợ tổng hợp giải thích nếu cần.
- **Phương án đã chọn:** Phương án B (Deterministic Python Rules Engine).
- **Lý do:** Trong thi đấu AI, việc làm tròn tiền tệ và đánh giá logic timestamp bắt buộc phải đạt độ chính xác $100\%$. LLM có rủi ro bị hallucinations (ảo giác) làm sai lệch tiền hoàn hoặc trích xuất sai root cause code, dẫn đến bị tính 0 điểm (hard gate failure).
- **Bằng chứng quyết định phù hợp:** Kết quả chạy 50 case chính thức đạt $100\%$ tính hợp lệ, không có bất kỳ case nào bị lỗi quy tắc hoặc sai số tiền tệ.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  AssertionError: assert 115.00000000000001 == 115.0
  ```
- **Lệnh hoặc bước tái hiện:** Chạy testcase đối soát split payment với `payment_total = 115.0` và `items + freight = 100.0 + 15.0`.
- **Nguyên nhân gốc:** Phép cộng số thực (`float`) chuẩn IEEE 754 trong Python gây ra hiện tượng trôi số thập phân (`floating-point inaccuracy`), làm cho phép so sánh bằng trực tiếp `==` hoặc phép trừ khoảng sai số bị lệch.
- **Cách xử lý:** Chuyển toàn bộ phép tính tiền tệ trong `utils/money.py` sang dùng `decimal.Decimal` với chế độ làm tròn `ROUND_HALF_UP`:
  ```python
  def format_brl(value: float) -> float:
      d = Decimal(str(value))
      return float(d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
  ```
- **Cách xác minh sau khi sửa:** Chuyển qua dùng `format_brl()` và `is_within_split_tolerance()`, chạy lại `pytest tests/test_policy_agent.py` đạt kết quả `PASSED`.
- **Điều học được:** Khi xử lý bài toán tài chính/thương mại điện tử, không bao giờ dùng trực tiếp kiểu `float` thô để so sánh giá trị tiền tệ.

---

## 7. Hiểu biết về luồng end-to-end

1. Khi hệ thống nhận file `EC_xxx.json` chứa `claimed_order_id`, `CoordinatorAgent` điều phối luồng xử lý.
2. `OrderAgent` truy vấn bảng `orders` và `order_items` lấy danh sách món hàng, seller và các mốc thời gian bàn giao.
3. `PaymentAgent` đối soát bảng `order_payments` để tính tổng tiền thanh toán thực tế của khách hàng.
4. `DeliveryAgent` so sánh thời gian giao thực tế với thời gian dự kiến và mốc bàn giao của seller.
5. Bộ 3 context này được chuyển tới `PolicyAgent` (do tôi phụ trách) để đối chiếu cây luật `EC_POLICY_V1`, đưa ra quyết định hoàn tiền và nguyên nhân gốc.
6. `VerifierAgent` nhận kết quả, kiểm tra lại toàn bộ schema, entity bounds ($\le 5$), syntax evidence IDs ($\le 10$) và ghi kết quả ra file `output/EC_xxx.json`.

---

## 8. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Lê Nguyễn Phi Trường  
**Ngày xác nhận:** 2026-08-05
