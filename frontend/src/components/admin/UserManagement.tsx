import React, { useState, useEffect, useCallback, memo } from 'react';
import {
  UsersIcon,
  PencilIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  UserCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import { adminService } from '../../services/admin.service';
import { UserManagement as UserManagementType } from '../../types/api';
import { Modal, Button } from '../ui';
import { useModal } from '../../hooks/useModal';
import { useErrorHandler } from '../../hooks/useErrorHandler';
import LoadingSpinner from '../common/LoadingSpinner';

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<UserManagementType[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [editingUser, setEditingUser] = useState<UserManagementType | null>(null);
  const [newRole, setNewRole] = useState<string>('');
  const [updating, setUpdating] = useState(false);

  const editModal = useModal();
  const { error, setError, handleError } = useErrorHandler();

  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminService.getUsersForManagement(roleFilter || undefined);
      setUsers(data);
    } catch (err) {
      console.error('Failed to load users:', err);
      handleError(err);
    } finally {
      setLoading(false);
    }
  }, [roleFilter, handleError, setError]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const handleRoleUpdate = async () => {
    if (!editingUser || !newRole) return;

    try {
      setUpdating(true);
      await adminService.updateUserRole(editingUser.id, newRole);

      // Update local state
      setUsers(
        users.map(user => (user.id === editingUser.id ? { ...user, role: newRole as any } : user))
      );

      setEditingUser(null);
      setNewRole('');
    } catch (err) {
      console.error('Failed to update user role:', err);
      handleError(err);
    } finally {
      setUpdating(false);
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (
      !window.confirm('Are you sure you want to delete this user? This action cannot be undone.')
    ) {
      return;
    }

    try {
      await adminService.deleteUser(userId);
      setUsers(users.filter(user => user.id !== userId));
    } catch (err) {
      console.error('Failed to delete user:', err);
      handleError(err);
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch =
      user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-red-100 text-red-800';
      case 'sworik_developer':
        return 'bg-purple-100 text-purple-800';
      case 'contributor':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <UsersIcon className="h-8 w-8 text-primary" />
          <h2 className="text-2xl font-bold text-foreground">User Management</h2>
        </div>
        <Button onClick={loadUsers} variant="primary">
          Refresh
        </Button>
      </div>

      {error && (
        <div className="bg-destructive border border-destructive-border rounded-lg p-4">
          <div className="flex items-center">
            <XCircleIcon className="h-5 w-5 text-destructive-foreground mr-2" />
            <p className="text-destructive-foreground">{error}</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-card rounded-lg shadow-md p-6 border border-border">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-accent" />
            <input
              type="text"
              placeholder="Search users..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 w-full border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-transparent"
            />
          </div>
          <select
            value={roleFilter}
            onChange={e => setRoleFilter(e.target.value)}
            className="px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-transparent"
          >
            <option value="">All Roles</option>
            <option value="contributor">Contributors</option>
            <option value="admin">Admins</option>
            <option value="sworik_developer">Sworik Developers</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-card rounded-lg shadow-md border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-background">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                  Activity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                  Joined
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-card divide-y divide-border">
              {filteredUsers.map(user => (
                <tr key={user.id} className="hover:bg-background">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <UserCircleIcon className="h-10 w-10 text-gray-600" />
                      <div className="ml-4">
                        <div className="text-sm font-medium text-foreground">{user.name}</div>
                        <div className="text-sm text-secondary-foreground">{user.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleColor(user.role)}`}
                    >
                      {user.role.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                    <div>
                      <p>Recordings: {user.recordings_count}</p>
                      <p>Transcriptions: {user.transcriptions_count}</p>
                      <p>Reviews: {user.quality_reviews_count}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-foreground">
                    {formatDate(user.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <Button
                        onClick={() => {
                          setEditingUser(user);
                          setNewRole(user.role);
                          editModal.open();
                        }}
                        variant="outline"
                        size="sm"
                        className="text-primary hover:text-primary-hover border-0"
                      >
                        <PencilIcon className="h-5 w-5" />
                      </Button>
                      <Button
                        onClick={() => handleDeleteUser(user.id)}
                        variant="outline"
                        size="sm"
                        className="text-destructive hover:text-destructive-hover border-0"
                      >
                        <TrashIcon className="h-5 w-5" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredUsers.length === 0 && (
          <div className="text-center py-12">
            <UsersIcon className="mx-auto h-12 w-12 text-accent" />
            <h3 className="mt-2 text-sm font-medium text-foreground">No users found</h3>
            <p className="mt-1 text-sm text-secondary-foreground">
              {searchTerm || roleFilter ? 'Try adjusting your filters.' : 'No users available.'}
            </p>
          </div>
        )}
      </div>

      {/* Edit Role Modal */}
      <Modal
        isOpen={editModal.isOpen && !!editingUser}
        onClose={() => {
          setEditingUser(null);
          setNewRole('');
          editModal.close();
        }}
        title="Edit User Role"
        size="sm"
      >
        <div className="mb-4">
          <p className="text-sm text-secondary-foreground mb-2">User: {editingUser?.name}</p>
          <p className="text-sm text-secondary-foreground mb-4">Email: {editingUser?.email}</p>
          <label className="block text-sm font-medium text-secondary-foreground mb-2">Role</label>
          <select
            value={newRole}
            onChange={e => setNewRole(e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-transparent"
          >
            <option value="contributor">Contributor</option>
            <option value="admin">Admin</option>
            <option value="sworik_developer">Sworik Developer</option>
          </select>
        </div>
        <div className="flex justify-end space-x-3">
          <Button
            onClick={() => {
              setEditingUser(null);
              setNewRole('');
              editModal.close();
            }}
            variant="outline"
            disabled={updating}
          >
            Cancel
          </Button>
          <Button
            onClick={handleRoleUpdate}
            disabled={updating || newRole === editingUser?.role}
            variant="primary"
            isLoading={updating}
          >
            Update Role
          </Button>
        </div>
      </Modal>
    </div>
  );
};

export default memo(UserManagement);
