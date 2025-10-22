"""
数据库模块
使用SQLAlchemy ORM进行数据库操作
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Optional, Generator
import os

from ..config import get_settings

# 创建基础模型类
Base = declarative_base()


class QuestionAnswer(Base):
    """问题答案表模型"""
    __tablename__ = "question_answer"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="记录ID")
    question = Column(String(1000), nullable=False, comment="问题内容")
    answer = Column(Text, nullable=False, comment="答案内容")
    options = Column(Text, default="", comment="选项内容")
    type = Column(String(50), default="", comment="问题类型")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<QuestionAnswer(id={self.id}, question='{self.question[:50]}...')>"


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.settings = get_settings()
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()

    def _initialize_engine(self):
        """初始化数据库引擎"""
        try:
            # 获取数据库配置
            db_config = self.settings.database

            # 创建数据库目录（如果不存在）
            db_path = db_config.url.replace("sqlite:///", "")
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

            # 创建引擎
            if db_config.url.startswith("sqlite"):
                # SQLite特殊配置
                self.engine = create_engine(
                    db_config.url,
                    echo=db_config.echo,
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 20
                    }
                )
            else:
                # 其他数据库配置
                self.engine = create_engine(
                    db_config.url,
                    echo=db_config.echo,
                    pool_size=db_config.pool_size,
                    max_overflow=db_config.max_overflow
                )

            # 创建会话工厂
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )

            print(f"[数据库] 数据库引擎初始化成功: {db_config.url}")

        except Exception as e:
            print(f"[数据库] 数据库引擎初始化失败: {str(e)}")
            raise

    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("[数据库] 数据库表创建成功")
        except Exception as e:
            print(f"[数据库] 数据库表创建失败: {str(e)}")
            raise

    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话（依赖注入用）"""
        db = self.SessionLocal()
        try:
            yield db
        except Exception as e:
            db.rollback()
            print(f"[数据库] 会话异常: {str(e)}")
            raise
        finally:
            db.close()

    def get_connection(self) -> Session:
        """获取数据库连接"""
        return self.SessionLocal()

    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            from sqlalchemy import text
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print("[数据库] 数据库连接测试成功")
            return True
        except Exception as e:
            print(f"[数据库] 数据库连接测试失败: {str(e)}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            print("[数据库] 数据库连接已关闭")


class QuestionAnswerRepository:
    """问题答案仓储类"""

    def __init__(self, db: Session):
        self.db = db

    def find_by_question(self, question: str) -> Optional[QuestionAnswer]:
        """
        根据问题查找答案

        Args:
            question: 问题内容

        Returns:
            QuestionAnswer: 问题答案记录，如果不存在返回None
        """
        try:
            return self.db.query(QuestionAnswer).filter(
                QuestionAnswer.question == question
            ).first()
        except Exception as e:
            print(f"[数据库] 查询失败: {str(e)}")
            return None

    def create(self, question: str, answer: str, options: str = "", question_type: str = "") -> Optional[QuestionAnswer]:
        """
        创建新的问题答案记录

        Args:
            question: 问题内容
            answer: 答案内容
            options: 选项内容
            question_type: 问题类型

        Returns:
            QuestionAnswer: 创建的记录，如果创建失败返回None
        """
        try:
            # 检查是否已存在
            existing = self.find_by_question(question)
            if existing:
                print(f"[数据库] 问题已存在，更新答案: {question[:50]}...")
                existing.answer = answer
                existing.options = options
                existing.type = question_type
                self.db.commit()
                self.db.refresh(existing)
                return existing

            # 创建新记录
            qa_record = QuestionAnswer(
                question=question,
                answer=answer,
                options=options,
                type=question_type
            )

            self.db.add(qa_record)
            self.db.commit()
            self.db.refresh(qa_record)

            print(f"[数据库] 新记录创建成功: {question[:50]}...")
            return qa_record

        except Exception as e:
            self.db.rollback()
            print(f"[数据库] 创建记录失败: {str(e)}")
            return None

    def count_all(self) -> int:
        """
        统计所有记录数量

        Returns:
            int: 记录总数
        """
        try:
            return self.db.query(QuestionAnswer).count()
        except Exception as e:
            print(f"[数据库] 统计记录失败: {str(e)}")
            return 0

    def list_recent(self, limit: int = 10) -> list[QuestionAnswer]:
        """
        获取最近的记录

        Args:
            limit: 限制数量

        Returns:
            list[QuestionAnswer]: 记录列表
        """
        try:
            return self.db.query(QuestionAnswer).order_by(
                QuestionAnswer.created_at.desc()
            ).limit(limit).all()
        except Exception as e:
            print(f"[数据库] 获取最近记录失败: {str(e)}")
            return []

    def search_by_keyword(self, keyword: str, limit: int = 10) -> list[QuestionAnswer]:
        """
        根据关键词搜索问题

        Args:
            keyword: 搜索关键词
            limit: 限制数量

        Returns:
            list[QuestionAnswer]: 匹配的记录列表
        """
        try:
            return self.db.query(QuestionAnswer).filter(
                QuestionAnswer.question.contains(keyword)
            ).order_by(QuestionAnswer.created_at.desc()).limit(limit).all()
        except Exception as e:
            print(f"[数据库] 搜索失败: {str(e)}")
            return []


# 全局数据库管理器实例
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话（FastAPI依赖注入用）"""
    yield from db_manager.get_session()


def get_question_repository(db: Session) -> QuestionAnswerRepository:
    """获取问题答案仓储（FastAPI依赖注入用）"""
    return QuestionAnswerRepository(db)


def init_database():
    """初始化数据库"""
    try:
        # 创建表
        db_manager.create_tables()

        # 测试连接
        if db_manager.test_connection():
            print("[数据库] 数据库初始化完成")
            return True
        else:
            print("[数据库] 数据库连接测试失败")
            return False

    except Exception as e:
        print(f"[数据库] 数据库初始化失败: {str(e)}")
        return False