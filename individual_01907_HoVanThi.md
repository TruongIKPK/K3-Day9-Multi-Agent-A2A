# Member Role Report — Day 9: Multi Agent A2A

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin       | Nội dung     |
| --------------- | ------------ |
| Họ và tên       | Hồ Văn Thi  |
| MSSV            | 2A202601907       |
| Khóa/Lớp        | K3         |
| Vai trò chính   | QA & Verification Lead    |
| Ngày hoàn thành | 2026-08-05 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao   | Trạng thái                            |
| ------------------ | ------------------ | -------------- | ----------------- | ------------------------------------- |
| Kiểm tra đầu ra chuẩn hóa | `agents/verifier_agent.py`, `utils/validation.py` | `CaseInput`, `OrderContext`, `PaymentContext`, `PolicyDecision` | `FinalOutput` đã xác thực, đúng schema, đúng hard-gate | Hoàn thành |
| Đóng gói và xuất file kết quả | `services/export_service.py`, `services/dispute_service.py` | Danh sách case sau khi chạy coordinator và verifier | `output/EC_*.json` và `output.zip` | Hoàn thành |

Chỉ nhận ownership cho phần bạn trực tiếp thực hiện. Liên hệ rõ phần việc của bạn với đầu vào, đầu ra và các thành viên phụ thuộc vào phần đó.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                 | Thành viên/module được hỗ trợ | Kết quả                 |
| ------------------------- | ----------------------------- | ----------------------- |
| Kiểm tra tích hợp end-to-end | Toàn bộ pipeline `main.py` -> `DisputeService` -> các agent | Xác nhận trace, output JSON và packaging chạy đúng luồng batch |
| Rà soát tiêu chí chất lượng | `PolicyAgent` và `CoordinatorAgent` | Đối chiếu điều kiện hard-gate để bảo đảm output không vi phạm schema |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao          | Cách xác minh   |
| --------------------- | --------------------------- | ------------------------- | --------------- |
| Xây dựng bộ kiểm tra output | `utils/validation.py` | Bộ rule fail-fast cho giới hạn entity, evidence, confidence và tính nhất quán refund | `pytest tests/test_verifier.py` |
| Xây dựng verifier agent | `agents/verifier_agent.py` | `VerifierAgent` tạo `FinalOutput` hợp lệ trước khi ghi file | `pytest tests/test_verifier.py tests/test_golden_cases.py` |
| Xây dựng dịch vụ xuất kết quả | `services/export_service.py` | Ghi 50 file JSON đầu ra và tạo `output.zip` | Artifact trong `output/` và `output.zip` |
| Hỗ trợ kiểm tra pipeline batch | `services/dispute_service.py`, `main.py` | Xác nhận luồng chạy batch xử lý toàn bộ `input/EC_*.json` | `python main.py --mode all` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

50 file JSON hợp lệ trong thư mục `output/` và gói `output.zip`, không vi phạm hard-gate của verifier.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Phần verifier phải đóng vai trò lớp chặn cuối cùng để bảo đảm dữ liệu đi ra từ hệ thống là hợp lệ, có thể nộp được, và không làm hỏng bộ kết quả batch khi một case đầu vào có dữ liệu thiếu hoặc bất nhất.

### Cách triển khai

`VerifierAgent` nhận output tạm từ các agent trước đó rồi áp các hard-gate trong `utils/validation.py`. Các kiểm tra tập trung vào giới hạn kích thước dữ liệu, tính hợp lệ của confidence/evidence id, và sự nhất quán giữa trạng thái case với số tiền hoàn trả. Nếu output không đạt, verifier trả lỗi sớm thay vì cho ghi xuống file. Sau khi qua kiểm tra, `ExportService` ghi file `output/EC_*.json` và đóng gói toàn bộ kết quả thành `output.zip`.

### Input, output và contract

| Thành phần              | Mô tả                                  |
| ----------------------- | -------------------------------------- |
| Input                   | `CaseInput` và các context từ `OrderAgent`, `PaymentAgent`, `DeliveryAgent`, `PolicyAgent` |
| Output                  | `FinalOutput` hợp lệ, có thể serialize sang JSON |
| Module phụ thuộc        | `agents/policy_agent.py`, `core/models.py`, `agents/coordinator_agent.py` |
| Module sử dụng output   | `services/export_service.py`, `services/dispute_service.py` |
| Điều kiện lỗi cần xử lý | Output vượt giới hạn entity/evidence, confidence ngoài khoảng, refund không khớp với trạng thái case, thiếu field bắt buộc |

### Cách xác minh

```bash
pytest tests/test_verifier.py tests/test_golden_cases.py
python main.py --mode all
```

- **Kết quả mong đợi:** Verifier chặn output sai, các case hợp lệ được xuất thành JSON và đóng gói thành công.
- **Kết quả thực tế:** Luồng batch sinh ra đủ file `output/EC_*.json` và `output.zip` khi các case qua kiểm tra.
- **Artifact/log:** `output/`, `output.zip`, `trace.jsonl`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần chọn cách kiểm tra output ở bước cuối để tránh ghi ra dữ liệu lỗi hoặc dữ liệu vượt giới hạn schema.
- **Các phương án đã cân nhắc:** Cho ghi file rồi kiểm tra sau; hoặc kiểm tra fail-fast trước khi xuất file.
- **Phương án đã chọn:** Kiểm tra fail-fast trong verifier trước khi export.
- **Lý do:** Cách này giảm nguy cơ phát tán output sai, giữ pipeline ổn định và giúp lỗi được phát hiện ngay tại điểm phát sinh.
- **Bằng chứng quyết định phù hợp:** Bộ test verifier và golden cases, cùng việc batch output vẫn đạt schema compliance khi chạy toàn bộ luồng.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Một số output có nguy cơ không khớp giữa trạng thái case và giá trị hoàn tiền, hoặc không đạt giới hạn hard-gate.
- **Lệnh hoặc bước tái hiện:** Chạy verifier trên batch case và kiểm tra các file `output/EC_*.json`.
- **Nguyên nhân gốc:** Output từ các bước trước chưa được chặn đủ chặt trước khi ghi file.
- **Cách xử lý:** Bổ sung lớp kiểm tra xác thực ở verifier và chỉ cho phép export khi output đã hợp lệ.
- **Cách xác minh sau khi sửa:** `pytest tests/test_verifier.py tests/test_golden_cases.py` và chạy `python main.py --mode all`.
- **Điều học được:** Verifier phải là lớp bảo vệ cuối cùng của pipeline, không nên để trách nhiệm kiểm tra dồn hoàn toàn sang bước export.

Nếu chưa xử lý xong:

- **Phạm vi bị ảnh hưởng:** `agents/verifier_agent.py`, `utils/validation.py`, `services/export_service.py`.
- **Những gì đã loại trừ:** Lỗi không nằm ở phần đọc CSV hay phần policy rules, vì output sai chỉ xuất hiện ở bước cuối trước khi ghi file.
- **Bước tiếp theo:** Mở rộng test golden cases để bao phủ thêm các trường hợp output biên.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ input case đến output JSON như thế nào?
2. Ground truth và bộ test golden được dùng để đo chất lượng đầu ra ra sao?
3. Quality checks khác với việc đóng gói output ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

Trong bài này, mỗi file `input/EC_*.json` được `main.py` và `DisputeService` đọc vào thành `CaseInput`, rồi coordinator điều phối lần lượt `OrderAgent`, `PaymentAgent`, `DeliveryAgent`, `PolicyAgent` và cuối cùng là `VerifierAgent`. Sau khi verifier chấp nhận output, `ExportService` ghi ra `output/EC_*.json`; ở chế độ batch, toàn bộ kết quả còn được nén thành `output.zip` và trace được ghi vào `trace.jsonl`.

Bộ golden cases dùng như mốc đối chiếu để xác nhận output có đúng cấu trúc, đúng giới hạn hard-gate và đúng logic nghiệp vụ của từng case hay không. Trong ngữ cảnh bài này, quality checks là các luật xác thực trong verifier; còn packaging chỉ là bước ghi file và đóng gói sau khi output đã được xác nhận hợp lệ.

Phải dùng cùng một test set cho baseline, corrupted và repaired để phép so sánh công bằng, tránh thay đổi dữ liệu đầu vào làm sai lệch kết quả. Repair được xem là thành công khi artifact đầu ra hợp lệ, tất cả file JSON qua schema, không còn hard-gate failure, và batch vẫn tạo được `output.zip` ổn định.

## 8. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Hồ Văn Thi
**Ngày xác nhận:** 2026-08-05
