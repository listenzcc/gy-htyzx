# auth_manager.py
import re
from omegaconf import OmegaConf
from sqlalchemy.orm import Session
from typing import List, Optional
from .models import User, Permission, RoleEnum, Base

PERMISSIONS = OmegaConf.load('./conf/permission.yml')['permissions']


class PermissionManager:
    """权限管理器"""

    PERMISSIONS = PERMISSIONS

    # 角色默认权限
    ROLE_PERMISSIONS = {
        RoleEnum.GUEST.value: [e['name'] for e in PERMISSIONS if 'GUEST' in e['roles']],
        RoleEnum.USER.value: [e['name'] for e in PERMISSIONS if 'USER' in e['roles']],
        RoleEnum.ADMIN.value: [e['name'] for e in PERMISSIONS if 'ADMIN' in e['roles']],
    }

    def __init__(self, session: Session):
        self.session = session

    def initialize_permissions(self):
        """初始化权限到数据库"""
        # for perm_name, description in self.PERMISSIONS.items():
        for perm in self.PERMISSIONS:
            perm_name = perm['name']
            description = perm['description']
            if not self.session.query(Permission).filter_by(name=perm_name).first():
                permission = Permission(
                    name=perm_name, description=description)
                self.session.add(permission)
        self.session.commit()

    def assign_role_permissions(self, user: User):
        """为用户分配角色对应的默认权限"""
        # 清除现有权限
        user.permissions.clear()

        # 分配新权限
        if user.role in self.ROLE_PERMISSIONS:
            for perm_name in self.ROLE_PERMISSIONS[user.role]:
                permission = self.session.query(
                    Permission).filter_by(name=perm_name).first()
                if permission and permission not in user.permissions:
                    user.permissions.append(permission)

        self.session.commit()

    def add_permission_to_user(self, user_id: int, permission_name: str) -> bool:
        """为用户添加单个权限"""
        user = self.session.query(User).get(user_id)
        permission = self.session.query(Permission).filter_by(
            name=permission_name).first()

        if user and permission and permission not in user.permissions:
            user.permissions.append(permission)
            self.session.commit()
            return True
        return False

    def remove_permission_from_user(self, user_id: int, permission_name: str) -> bool:
        """移除用户的单个权限"""
        user = self.session.query(User).get(user_id)
        permission = self.session.query(Permission).filter_by(
            name=permission_name).first()

        if user and permission and permission in user.permissions:
            user.permissions.remove(permission)
            self.session.commit()
            return True
        return False

    def check_permission(self, user: User, permission_name: str) -> bool:
        """检查用户是否有特定权限"""
        # 管理员自动拥有所有权限
        if user.is_admin():
            return True

        return user.has_permission(permission_name)

    def check_permission_pattern(self, user: User, pattern: str) -> bool:
        """使用正则表达式检查权限模式"""
        # 管理员自动通过
        if user.is_admin():
            return True

        # 检查是否有匹配的权限
        for permission in user.permissions:
            if re.match(pattern, permission.name):
                return True
        return False
