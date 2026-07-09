# user_service.py
import sys
from uuid import uuid4
from typing import Optional, List, Union
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .models import User, RoleEnum
from .auth_manager import PermissionManager
from . import logger

sys.path.append('..')  # noqa
from constants import *


class UserService:
    """用户管理服务"""

    def __init__(self, session: Session):
        self.session = session
        self.permission_manager = PermissionManager(session)

    def create_user(self, username: str, password: str,
                    role: str = RoleEnum.GUEST.value, **kwargs) -> Optional[User]:
        """创建新用户"""
        try:
            # 检查用户名和邮箱是否已存在
            if self.session.query(User).filter(
                or_(User.username == username)
            ).first():
                logger.error(f"用户名已存在: {username}")
                return None

            # 创建用户
            user = User(username=username, role=role,
                        uuid=str(uuid4()), **kwargs)
            user.set_password(password)

            self.session.add(user)
            self.session.commit()

            # 分配角色对应的默认权限
            self.permission_manager.assign_role_permissions(user)

            logger.info(f"用户创建成功: {username}")
            return user

        except Exception as e:
            self.session.rollback()
            logger.error(f"创建用户失败: {e}")
            return None

    def authenticate_user(self, identifier: str, password: str) -> Optional[User]:
        """用户认证"""
        user = self.session.query(User).filter(
            or_(User.username == identifier)
        ).first()

        if user and user.check_password(password) and user.is_active:
            user.last_login = datetime.now()
            self.session.commit()
            return user

        return None

    def update_user_role(self, user_id: int, new_role: str) -> bool:
        """更新用户角色"""
        try:
            user = self.session.query(User).get(user_id)
            if not user:
                return False

            old_role = user.role
            user.role = new_role

            # 重新分配权限
            self.permission_manager.assign_role_permissions(user)

            self.session.commit()
            logger.info(
                f"用户角色更新: {user.username} {old_role} -> {new_role}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"更新用户角色失败: {e}")
            return False

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.session.query(User).get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.session.query(User).filter_by(username=username).first()

    def list_users(self, role: str = None, active_only: bool = False) -> List[User]:
        """列出用户"""
        query = self.session.query(User)

        if role:
            query = query.filter_by(role=role)

        if active_only:
            query = query.filter_by(is_active=True)

        return query.order_by(User.created_at.desc()).all()

    def deactivate_user(self, user_id: int) -> bool:
        """停用用户"""
        try:
            user = self.session.query(User).get(user_id)
            user.is_active = False
            self.session.commit()
            logger.info(f"用户已停用: {user.username}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"停用用户失败: {e}")
            return False

    def activate_user(self, user_id: int) -> bool:
        """激活用户"""
        try:
            user = self.session.query(User).get(user_id)
            user.is_active = True
            self.session.commit()
            logger.info(f"用户已激活: {user.username}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"激活用户失败: {e}")
            return False

    def edit_user_comprehensive(self, updated: dict):
        """一次编辑多项用户信息"""
        try:
            user = self.session.query(User).get(updated['id'])

            from datetime import datetime

            # Change every input
            user.role = updated['role']
            user.gender = updated['gender']
            user.is_active = updated['is_active']
            user.education = updated['education']
            user.birth_date = datetime.strptime(
                updated['birth_date'], DATE_FMT)
            user.training_date = datetime.strptime(
                updated['training_date'], DATE_FMT)

            self.session.commit()
            logger.info(f"用户信息已修改: {updated}")

            if updated.get('password'):
                user.set_password(updated['password'])
                self.session.commit()
                logger.info(f"用户密码已修改: {user.username}")

            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f'修改用户信息失败: {e}')
            return False

    def reset_user_passwd(self, identifier: Union[str, int], password):
        """重置用户密码
        Args:
            identifier: 用户ID(int)或用户名/邮箱(str)
            passwd: 新密码
        Returns:
            bool: 修改成功返回True，失败返回False
        """
        try:

            # 根据标识符类型查询用户
            if isinstance(identifier, int):
                # 按用户ID查找
                user = self.session.query(User).filter(
                    User.id == identifier).first()
            else:
                # 按用户名或邮箱查找
                user = self.session.query(User).filter(
                    or_(User.username == identifier, User.email == identifier)
                ).first()

            user.set_password(password)
            self.session.commit()

            logger.info(f"用户密码修改成功: {user.username} (ID: {user.id})")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"修改密码失败: {e}")
            return False
        pass

    def remove_user(self, identifier: Union[str, int]) -> bool:
        """删除用户
        Args:
            identifier: 用户ID(int)或用户名/邮箱(str)
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        try:
            # 根据标识符类型查询用户
            if isinstance(identifier, int):
                # 按用户ID查找
                user = self.session.query(User).filter(
                    User.id == identifier).first()
            else:
                # 按用户名或邮箱查找
                user = self.session.query(User).filter(
                    or_(User.username == identifier, User.email == identifier)
                ).first()

            if not user:
                logger.error(f"用户不存在: {identifier}")
                return False

            # 检查是否允许删除（例如不能删除最后一个管理员）
            if self._should_prevent_deletion(user):
                logger.error(f"不允许删除用户: {user.username}")
                return False

            # 先删除相关依赖数据（根据你的数据库关系）
            self._cleanup_user_dependencies(user)

            # 删除用户
            self.session.delete(user)
            self.session.commit()

            logger.info(f"用户删除成功: {user.username} (ID: {user.id})")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"删除用户失败: {e}")
            return False

    def _should_prevent_deletion(self, user: User) -> bool:
        """检查是否应该阻止删除用户"""
        # 防止删除最后一个管理员
        if user.role == RoleEnum.ADMIN.value:
            admin_count = self.session.query(User).filter(
                User.role == RoleEnum.ADMIN.value
            ).count()
            return admin_count <= 1

        # 添加其他阻止删除的条件
        # if user.username == 'admin':
        #     return True

        return False

    def _cleanup_user_dependencies(self, user: User) -> None:
        """清理用户的关联数据"""
        try:
            # 示例：删除用户的权限记录
            # 假设你的权限管理器有清理方法
            if hasattr(self.permission_manager, 'remove_user_permissions'):
                self.permission_manager.remove_user_permissions(user)

            # 示例：如果用户有相关订单、文章等，可以在这里清理
            # orders = self.session.query(Order).filter(Order.user_id == user.id).all()
            # for order in orders:
            #     self.session.delete(order)

            # 注意：如果数据库有外键约束且设置了级联删除，这部分可能不需要
            logger.debug(f"已清理用户 {user.username} 的关联数据")

        except Exception as e:
            logger.warning(f"清理用户关联数据时出错: {e}")
            # 可以选择继续删除或抛出异常
