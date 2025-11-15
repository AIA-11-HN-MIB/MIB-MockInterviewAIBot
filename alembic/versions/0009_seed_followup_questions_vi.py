"""Seed follow-up questions in Vietnamese

Revision ID: 0009
Revises: 0008
Create Date: 2025-01-15 00:00:00
"""
from typing import Sequence, Union
from datetime import datetime, timedelta
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, Column, MetaData
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime


# revision identifiers, used by Alembic.
revision: str = '0009'
down_revision: Union[str, Sequence[str], None] = '0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed follow-up questions in Vietnamese."""

    metadata = MetaData()
    now = datetime.utcnow()

    follow_up_questions_table = Table(
        'follow_up_questions', metadata,
        Column('id', UUID(as_uuid=True)),
        Column('parent_question_id', UUID(as_uuid=True)),
        Column('interview_id', UUID(as_uuid=True)),
        Column('text', Text),
        Column('generated_reason', Text),
        Column('order_in_sequence', Integer),
        Column('created_at', DateTime),
    )

    # =============================================
    # SEED DATA - FOLLOW-UP QUESTIONS (Vietnamese)
    # =============================================
    follow_up_data = [
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440001'),
            'parent_question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440001'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440001'),
            'text': 'Bạn đã đề cập đến sự khác biệt về scope. Bạn có thể giải thích hoisting là gì trong JavaScript và nó khác nhau như thế nào giữa var, let và const?',
            'generated_reason': 'Thiếu khái niệm chính: hành vi hoisting. Câu trả lời đã đề cập scope nhưng không đề cập cách khai báo biến được hoisted khác nhau cho var so với let/const.',
            'order_in_sequence': 1,
            'created_at': now - timedelta(days=12, hours=2, minutes=7),
        },
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440002'),
            'parent_question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440001'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440001'),
            'text': 'Temporal Dead Zone (TDZ) là gì và nó liên quan như thế nào đến let và const?',
            'generated_reason': 'Thiếu khái niệm chính: Temporal Dead Zone. Câu trả lời không giải thích tại sao truy cập let/const trước khi khai báo ném ReferenceError, đây là khoảng trống hiểu biết quan trọng.',
            'order_in_sequence': 2,
            'created_at': now - timedelta(days=12, hours=2, minutes=8),
        },
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440003'),
            'parent_question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440007'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440001'),
            'text': 'Bạn đã đề cập useState và useEffect. Bạn có thể giải thích khi nào bạn sẽ sử dụng useMemo và useCallback, và chúng giải quyết vấn đề gì?',
            'generated_reason': 'Thiếu hooks tối ưu hóa: useMemo và useCallback. Câu trả lời đã đề cập các hooks cơ bản nhưng không thể hiện hiểu biết về hooks tối ưu hóa hiệu suất, điều quan trọng cho ứng dụng React.',
            'order_in_sequence': 1,
            'created_at': now - timedelta(days=12, hours=2, minutes=17),
        },
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440004'),
            'parent_question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440009'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440004'),
            'text': 'Bạn đã đề cập các phase của event loop. Bạn có thể giải thích sự khác biệt giữa microtask queue và macrotask queue, và chúng được xử lý như thế nào?',
            'generated_reason': 'Thiếu khái niệm chính: microtask vs macrotask queues. Câu trả lời đã đề cập các phase của event loop nhưng không giải thích sự khác biệt quan trọng giữa microtasks (Promise callbacks) và macrotasks (setTimeout), điều cần thiết để hiểu thứ tự thực thi async.',
            'order_in_sequence': 1,
            'created_at': now - timedelta(days=6, hours=2, minutes=47),
        },
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440005'),
            'parent_question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440003'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440004'),
            'text': 'Bạn đã giải thích async/await tốt. Làm thế nào bạn sẽ thực thi nhiều thao tác async song song, và bạn sẽ sử dụng gì cho điều đó?',
            'generated_reason': 'Thiếu pattern thực thi song song: Promise.all. Câu trả lời đã đề cập cách sử dụng async/await tuần tự nhưng không thể hiện hiểu biết về thực thi song song, một pattern tối ưu hóa phổ biến.',
            'order_in_sequence': 1,
            'created_at': now - timedelta(days=6, hours=3, minutes=13),
        },
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440006'),
            'parent_question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440002'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440005'),
            'text': 'Bạn đã đề cập Kubernetes cho orchestration. Bạn có thể giải thích service mesh là gì và nó giúp gì với giao tiếp microservices và observability?',
            'generated_reason': 'Thiếu khái niệm chính: service mesh. Câu trả lời cho thấy hiểu biết tốt về microservices và Kubernetes nhưng không đề cập các pattern service mesh, điều quan trọng cho kiến trúc microservices production.',
            'order_in_sequence': 1,
            'created_at': now - timedelta(days=4, hours=1, minutes=8),
        },
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440007'),
            'parent_question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440002'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440005'),
            'text': 'Làm thế nào bạn sẽ triển khai distributed tracing trên các microservices để debug các vấn đề trải dài trên nhiều services?',
            'generated_reason': 'Thiếu pattern observability: distributed tracing. Câu trả lời đã đề cập kiến trúc microservices nhưng không giải quyết cách trace requests qua ranh giới service, điều quan trọng để debug hệ thống phân tán.',
            'order_in_sequence': 2,
            'created_at': now - timedelta(days=4, hours=1, minutes=9),
        },
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440008'),
            'parent_question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440023'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440006'),
            'text': 'Bạn đã giải thích mô hình generational GC. Bạn có thể đặt tên và so sánh các thuật toán GC khác nhau có sẵn trong JVM, chẳng hạn như G1, Parallel và ZGC?',
            'generated_reason': 'Thiếu kiến thức chính: các thuật toán GC. Câu trả lời đã đề cập cơ bản về generational GC nhưng không thể hiện kiến thức về các thuật toán GC khác nhau và trade-offs của chúng, điều quan trọng cho JVM tuning.',
            'order_in_sequence': 1,
            'created_at': now - timedelta(days=2, hours=2, minutes=8),
        },
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440009'),
            'parent_question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440023'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440006'),
            'text': 'Làm thế nào bạn sẽ tối ưu hóa thời gian pause GC cho một ứng dụng low-latency? Bạn sẽ sử dụng những chiến lược nào?',
            'generated_reason': 'Thiếu kiến thức tối ưu hóa: giảm thời gian pause GC. Câu trả lời đã đề cập monitoring GC logs nhưng không đề cập các chiến lược để giảm thiểu thời gian pause, điều quan trọng cho ứng dụng nhạy cảm với độ trễ.',
            'order_in_sequence': 2,
            'created_at': now - timedelta(days=2, hours=2, minutes=9),
        },
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440010'),
            'parent_question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440005'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440007'),
            'text': 'Bạn đã giải thích hệ thống CP và AP tốt. Bạn có thể mô tả các mô hình consistency khác nhau, chẳng hạn như eventual consistency, strong consistency và causal consistency?',
            'generated_reason': 'Thiếu khái niệm chính: các mô hình consistency. Câu trả lời đã đề cập cơ bản về CAP theorem nhưng không giải thích các mô hình consistency khác nhau, điều quan trọng để hiểu cách hệ thống phân tán xử lý tính nhất quán dữ liệu.',
            'order_in_sequence': 1,
            'created_at': now - timedelta(days=1, hours=3, minutes=8),
        },
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440011'),
            'parent_question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440008'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440007'),
            'text': 'Bạn đã đề cập ba thế hệ. Bạn có thể giải thích chi tiết cách generational GC hoạt động trong Python, bao gồm các giá trị ngưỡng và tần suất collection cho mỗi thế hệ?',
            'generated_reason': 'Thiếu kiến thức chi tiết: chi tiết cụ thể về thế hệ GC. Câu trả lời đã đề cập cơ chế GC cơ bản nhưng không giải thích cách hoạt động chi tiết của generational GC, bao gồm các ngưỡng và chiến lược collection, điều quan trọng cho Python performance tuning.',
            'order_in_sequence': 1,
            'created_at': now - timedelta(days=1, hours=3, minutes=23),
        },
        {
            'id': uuid.UUID('b60e8400-e29b-41d4-a716-446655440012'),
            'parent_question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440008'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440007'),
            'text': 'Làm thế nào bạn sẽ điều chỉnh garbage collector của Python cho một ứng dụng high-throughput? Bạn sẽ điều chỉnh các hàm và tham số nào của module gc?',
            'generated_reason': 'Thiếu kiến thức thực tế: chiến lược tuning GC. Câu trả lời đã đề cập module gc nhưng không thể hiện hiểu biết về cách tune GC cho hiệu suất, điều quan trọng cho ứng dụng Python production.',
            'order_in_sequence': 2,
            'created_at': now - timedelta(days=1, hours=3, minutes=24),
        },
    ]

    op.bulk_insert(follow_up_questions_table, follow_up_data)
    print("[OK] Seeded 12 follow-up questions (Vietnamese)")


def downgrade() -> None:
    """Downgrade - delete seeded follow-up questions."""
    conn = op.get_bind()

    print("[INFO] Removing seeded follow-up questions...")
    conn.execute(sa.text("DELETE FROM follow_up_questions"))

    print("[OK] Follow-up questions removed")

