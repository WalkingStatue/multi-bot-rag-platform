/**
 * Collaborator invitation component
 */
import React, { useState, useEffect } from 'react';
import { CollaboratorInvite, CollaboratorInviteResponse } from '../../types/bot';
import { permissionService } from '../../services/permissionService';

interface CollaboratorInviteProps {
  botId: string;
  isOpen: boolean;
  onClose: () => void;
  onInviteSuccess: (response: CollaboratorInviteResponse) => void;
}

interface UserSearchResult {
  id: string;
  username: string;
  email: string;
  full_name?: string;
}

export const CollaboratorInviteModal: React.FC<CollaboratorInviteProps> = ({
  botId,
  isOpen,
  onClose,
  onInviteSuccess,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<UserSearchResult[]>([]);
  const [selectedUser, setSelectedUser] = useState<UserSearchResult | null>(null);
  const [selectedRole, setSelectedRole] = useState<'admin' | 'editor' | 'viewer'>('viewer');
  const [inviteMessage, setInviteMessage] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [isInviting, setIsInviting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTimeout, setSearchTimeout] = useState<NodeJS.Timeout | null>(null);

  // Clear state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setSearchQuery('');
      setSearchResults([]);
      setSelectedUser(null);
      setSelectedRole('viewer');
      setInviteMessage('');
      setError(null);
    }
  }, [isOpen]);

  // Debounced search
  useEffect(() => {
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }

    if (searchQuery.trim().length >= 2) {
      const timeout = setTimeout(() => {
        performSearch(searchQuery.trim());
      }, 300);
      setSearchTimeout(timeout);
    } else {
      setSearchResults([]);
    }

    return () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }
    };
  }, [searchQuery]);

  const performSearch = async (query: string) => {
    try {
      setIsSearching(true);
      setError(null);
      const results = await permissionService.searchUsers(query);
      setSearchResults(results);
    } catch (error: any) {
      console.error('Failed to search users:', error