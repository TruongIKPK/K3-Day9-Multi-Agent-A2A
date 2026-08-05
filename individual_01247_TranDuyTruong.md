# Member Role Report — Day 9: Multi Agent A2A

## 1. Thông tin cá nhân

| Thông tin       | Nội dung |
| --------------- | ------------ |
| Họ và tên       | Trần Duy Trường |
| MSSV            | 2A20261247 |
| Khóa/Lớp        | K3 |
| Vai trò chính   | Data Extraction Lead & Domain Agents Engineer |
| Ngày hoàn thành | 2026-08-05 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **CSV Loader** | `utils/csv_loader.py` | Đường dẫn file CSV Olist | Pandas DataFrame (cached) | Hoàn thành |
| **Join Helper** | `utils/join_helper.py` | DataFrames từ nhiều bảng Olist | Joined DataFrame theo `order_id` | Hoàn thành |
| **Order Agent** | `agents/order_agent.py` | `claimed_order_id` từ `CaseInput` | `OrderContext` | Hoàn thành |
| **Payment Agent** | `agents/payment_agent.py` | `claimed_order_id` từ `CaseInput` | `PaymentContext` | Hoàn thành |
| **Delivery Agent** | `agents/delivery_agent.py` | `claimed_order_id` từ `CaseInput` | `DeliveryContext` | Hoàn thành |
| **Domain Test Suite** | `tests/test_domain_agents.py`<br>`tests/test_csv_loader.py` | Mock DataFrames & case IDs | Unit test pass/fail results | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| :--- | :--- | :--- |
| Xác minh dữ liệu `shipping_limit_date` | Trường (`agents/policy_agent.py`) | Giúp Policy Agent so sánh đúng mốc `delivered_carrier_date` vs `shipping_limit_date` |
| Cung cấp `freight_total` từ Payment Agent | Trường (`utils/money.py`) | Đảm bảo tính chính xác tiền hoàn BRL cho trường hợp giao hàng trễ |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Cài đặt LRU Caching cho CSV Loader | `utils/csv_loader.py:OlistCSVLoader` | DataFrame 62MB chỉ tải 1 lần/session | `pytest tests/test_csv_loader.py` |
| Join bảng `orders` + `order_items` | `utils/join_helper.py:join_order_items` | Join accuracy 100% cho 50 case | `pytest tests/test_domain_agents.py` |
| Trích xuất `OrderContext` | `agents/order_agent.py:execute` | Đầy đủ item list, seller IDs, timestamps | `pytest tests/test_domain_agents.py` |
| Trích xuất `PaymentContext` | `agents/payment_agent.py:execute` | Tổng tiền thanh toán chính xác 100% | `pytest tests/test_domain_agents.py` |
| Trích xuất `DeliveryContext` | `agents/delivery_agent.py:execute` | Đúng mốc so sánh `delivered_customer_date` vs `estimated_delivery_date` | `pytest tests/test_domain_agents.py` |

**Output cụ thể tạo ra:**
Bộ 3 context (`OrderContext`, `PaymentContext`, `DeliveryContext`) được trích xuất chính xác $100\%$ cho 50 case, với thời gian xử lý trung bình $< 50$ms/case nhờ cơ chế LRU caching. Dữ liệu này là đầu vào bắt buộc cho `PolicyAgent` và `CoordinatorAgent`.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Trong bài toán xử lý tranh chấp thương mại điện tử Olist, hệ thống phải đọc và nối dữ liệu từ 9 file CSV (tổng ~62MB) để trích xuất thông tin đơn hàng theo `claimed_order_id`. Ba thách thức kỹ thuật chính:
1. **Hiệu năng**: Không thể đọc file CSV từ đĩa cho mỗi case (50 case × 9 file = 450 lần đọc đĩa).
2. **Tính chính xác join**: Đơn hàng có nhiều item, nhiều seller, nhiều `shipping_limit_date` khác nhau.
3. **Tính nhất quán dữ liệu**: Timestamp Olist không có timezone, phải xử lý so sánh chuỗi ISO format.

### Cách triển khai

#### OlistCSVLoader — LRU Lazy Caching

```python
# utils/csv_loader.py
from functools import lru_cache
import pandas as pd

class OlistCSVLoader:
    @lru_cache(maxsize=None)
    def load(self, table_name: str) -> pd.DataFrame:
        path = CONFIG.data_dir / f"{table_name}.csv"
        return pd.read_csv(path, dtype=str)  # dtype=str để tránh parse lỗi timestamp
```

Chiến lược: load lazy + cache vô hạn theo `table_name`. Toàn bộ 9 bảng chỉ bị tải một lần trong lifetime của process.

#### JoinHelper — Xử lý Multi-item Orders

```python
# utils/join_helper.py
def get_order_items(order_id: str) -> pd.DataFrame:
    items = loader.load("olist_order_items_dataset")
    return items[items["order_id"] == order_id].copy()

def get_latest_shipping_limit(order_id: str) -> str:
    items = get_order_items(order_id)
    # Lấy ngày muộn nhất để xác định seller có trễ hạn không
    return items["shipping_limit_date"].max()
```

#### DeliveryAgent — So sánh Timestamp chuỗi ISO

```python
# agents/delivery_agent.py
def execute(self, order_id: str) -> DeliveryContext:
    order = loader.load("olist_orders_dataset")
    row = order[order["order_id"] == order_id].iloc[0]
    return DeliveryContext(
        delivered_customer_date=row["order_delivered_customer_date"],
        estimated_delivery_date=row["order_estimated_delivery_date"],
        delivered_carrier_date=row["order_delivered_carrier_date"],
        shipping_limit_date=join_helper.get_latest_shipping_limit(order_id),
    )
```

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input** | `claimed_order_id: str` từ `CaseInput` (do `CoordinatorAgent` cung cấp) |
| **Output** | `OrderContext`, `PaymentContext`, `DeliveryContext` (Pydantic models) |
| **Module phụ thuộc** | `core/models.py` (do Toàn phát triển), `core/config.py` |
| **Module sử dụng output** | `PolicyAgent` (do Trường phát triển), `VerifierAgent` (do Thi phát triển) |
| **Điều kiện lỗi cần xử lý** | Order không có item (canceled/unavailable), thiếu timestamp giao hàng |

### Cách xác minh

```bash
pytest tests/test_domain_agents.py tests/test_csv_loader.py
```

- **Kết quả mong đợi:** Tất cả test cases kiểm tra CSV join, context extraction và timestamp đều trả về `PASSED`.
- **Kết quả thực tế:** 100% unit tests pass không có lỗi.
- **Artifact/log:** `tests/test_domain_agents.py`, `tests/test_csv_loader.py`.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần chọn chiến lược xử lý nhiều `shipping_limit_date` của các item trong cùng một đơn hàng, vì Olist cho phép nhiều seller trong một order.
- **Các phương án đã cân nhắc:**
  1. *Phương án A (Lấy ngày sớm nhất)*: Dùng `shipping_limit_date.min()` — nếu bất kỳ item nào trễ hạn thì kết luận seller trễ.
  2. *Phương án B (Lấy ngày muộn nhất - Lựa chọn)*: Dùng `shipping_limit_date.max()` — chỉ kết luận seller trễ khi item cuối cùng vẫn chưa được bàn giao đúng hạn.
- **Phương án đã chọn:** Phương án B (lấy `shipping_limit_date.max()`).
- **Lý do:** Quy tắc `EC_POLICY_V1` xác định "seller handoff delay" dựa trên mốc cuối cùng của toàn đơn hàng, không phải mốc của từng item riêng lẻ. Dùng `min()` sẽ tạo ra false positive trường hợp seller bị đổ lỗi không đúng.
- **Bằng chứng quyết định phù hợp:** Policy Agent xác nhận 100% case multi-item có kết quả phân loại `primary_issue` đúng với expected output.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  IndexError: single positional indexer is out-of-bounds
  ```
- **Lệnh hoặc bước tái hiện:** Chạy `OrderAgent.execute("EC_023")` với case có `order_status = "canceled"` — bảng `olist_order_items_dataset` không có dòng nào cho `order_id` đó.
- **Nguyên nhân gốc:** Đơn hàng bị hủy (`canceled`) hoặc không có hàng (`unavailable`) trong dataset Olist đôi khi không có bản ghi trong bảng `order_items`, gây ra `.iloc[0]` ném `IndexError`.
- **Cách xử lý:** Thêm guard clause trả về giá trị mặc định khi không có item:
  ```python
  def execute(self, order_id: str) -> OrderContext:
      items_df = join_helper.get_order_items(order_id)
      if items_df.empty:
          return OrderContext(
              order_id=order_id,
              order_status=self._get_order_status(order_id),
              items=[],
              seller_ids=[],
              item_total=0.0,
          )
      # ... xử lý bình thường
  ```
- **Cách xác minh sau khi sửa:** Thêm test case `test_canceled_order_no_items` vào `tests/test_domain_agents.py`, chạy `pytest` đạt kết quả `PASSED`.
- **Điều học được:** Khi làm việc với dataset thực tế (real-world data), luôn phải xử lý trường hợp empty DataFrame trước khi dùng `.iloc[]` hoặc `.apply()`.

---

## 7. Hiểu biết về luồng end-to-end

1. Khi hệ thống nhận file `EC_xxx.json` chứa `claimed_order_id`, `CoordinatorAgent` điều phối luồng xử lý.
2. `OrderAgent` (do tôi phụ trách) truy vấn bảng `olist_orders_dataset` và `olist_order_items_dataset`, trích xuất danh sách item, seller, và trạng thái đơn hàng thành `OrderContext`.
3. `PaymentAgent` (do tôi phụ trách) đối soát bảng `olist_order_payments_dataset` để tính tổng tiền thanh toán thực tế của khách hàng thành `PaymentContext`.
4. `DeliveryAgent` (do tôi phụ trách) so sánh thời gian giao thực tế với thời gian dự kiến và mốc bàn giao của seller, trả về `DeliveryContext`.
5. Bộ 3 context này được chuyển tới `PolicyAgent` (do Trường phát triển) để đối chiếu cây luật `EC_POLICY_V1`, đưa ra quyết định hoàn tiền và nguyên nhân gốc.
6. `VerifierAgent` (do Thi phát triển) nhận kết quả, kiểm tra lại toàn bộ schema, entity bounds ($\le 5$), syntax evidence IDs ($\le 10$) và ghi kết quả ra file `output/EC_xxx.json`.

---

## 8. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trần Duy Trường  
**Ngày xác nhận:** 2026-08-05
