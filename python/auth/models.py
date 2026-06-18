# models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
import enum

Base = declarative_base()


class RoleEnum(enum.Enum):
    """角色枚举"""
    GUEST = "GUEST"
    USER = "USER"
    ADMIN = "ADMIN"


# 权限关联表（多对多关系）
user_permissions = Table('user_permissions', Base.metadata,
                         Column('user_id', Integer, ForeignKey(
                             'users.id'), primary_key=True),
                         Column('permission_id', Integer, ForeignKey(
                             'permissions.id'), primary_key=True)
                         )


class Permission(Base):
    """权限模型"""
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)  # 权限名称
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    users = relationship('User', secondary=user_permissions,
                         back_populates='permissions')


class User(Base):
    """用户模型"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    role = Column(String(20), default=RoleEnum.GUEST.value, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    username = Column(String(50), unique=True, nullable=False)
    education = Column(String(50), unique=False, nullable=True)
    gender = Column(String(10), unique=False, nullable=True)
    training_date = Column(DateTime, unique=False, nullable=True)

    password_hash = Column(String(255), nullable=False)

    # 关系
    permissions = relationship(
        'Permission', secondary=user_permissions, back_populates='users')

    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        """检查用户是否具有指定角色"""
        return self.role == role_name

    def has_permission(self, permission_name):
        """检查用户是否具有指定权限"""
        return any(perm.name == permission_name for perm in self.permissions)

    def is_admin(self):
        """检查是否是管理员"""
        return self.role == RoleEnum.ADMIN.value

    def to_dict(self):
        """转换为字典（排除敏感信息）"""
        return {
            # ------------------------------------------------------------------
            # 个人信息
            'name': self.name,                    # 姓名
            'birth_date': self.birth_date,        # 出生日期
            'education': self.education,          # 学历
            'gender': self.gender,                # 性别
            'training_date': self.training_date,  # 受训时间
            # ------------------------------------------------------------------
            # 系统内置
            'id': self.id,
            'role': self.role,                    # 角色
            'is_active': self.is_active,          # 是否激活
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
