/**
 * Unit tests for validation utilities
 */
import { describe, it, expect } from 'vitest';
import { 
  validateField, 
  validateForm, 
  authValidationRules, 
  validateConfirmPassword 
} from '../../utils/validators';

describe('validators', () => {
  describe('validateField', () => {
    it('should validate required fields', () => {
      expect(validateField('', { required: true })).toBe('This field is required');
      expect(validateField('   ', { required: true })).toBe('This field is required');
      expect(validateField('value', { required: true })).toBeNull();
    });

    it('should validate minimum length', () => {
      expect(validateField('ab', { minLength: 3 })).toBe('Must be at least 3 characters');
      expect(validateField('abc', { minLength: 3 })).toBeNull();
      expect(validateField('abcd', { minLength: 3 })).toBeNull();
    });

    it('should validate maximum length', () => {
      expect(validateField('abcdef', { maxLength: 5 })).toBe('Must be no more than 5 characters');
      expect(validateField('abcde', { maxLength: 5 })).toBeNull();
      expect(validateField('abcd', { maxLength: 5 })).toBeNull();
    });

    it('should validate pattern', () => {
      const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      expect(validateField('invalid-email', { pattern: emailPattern })).toBe('Invalid format');
      expect(validateField('valid@email.com', { pattern: emailPattern })).toBeNull();
    });

    it('should validate custom rules', () => {
      const customRule = {
        custom: (value: string) => value === 'forbidden' ? 'This value is not allowed' : null,
      };
      
      expect(validateField('forbidden', customRule)).toBe('This value is not allowed');
      expect(validateField('allowed', customRule)).toBeNull();
    });

    it('should skip validation for empty optional fields', () => {
      expect(validateField('', { minLength: 3 })).toBeNull();
      expect(validateField('', { pattern: /\d+/ })).toBeNull();
    });
  });

  describe('validateForm', () => {
    it('should validate multiple fields', () => {
      const data = {
        username: 'ab',
        email: 'invalid-email',
        password: '',
      };

      const rules = {
        username: { required: true, minLength: 3 },
        email: { required: true, pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/ },
        password: { required: true },
      };

      const errors = validateForm(data, rules);

      expect(errors.username).toBe('Must be at least 3 characters');
      expect(errors.email).toBe('Invalid format');
      expect(errors.password).toBe('This field is required');
    });

    it('should return empty object for valid data', () => {
      const data = {
        username: 'validuser',
        email: 'valid@email.com',
        password: 'password123',
      };

      const rules = {
        username: { required: true, minLength: 3 },
        email: { required: true, pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/ },
        password: { required: true },
      };

      const errors = validateForm(data, rules);

      expect(Object.keys(errors)).toHaveLength(0);
    });
  });

  describe('authValidationRules', () => {
    it('should validate username correctly', () => {
      expect(validateField('ab', authValidationRules.username)).toBe('Must be at least 3 characters');
      expect(validateField('invalid username!', authValidationRules.username)).toBe('Invalid format');
      expect(validateField('valid_username-123', authValidationRules.username)).toBeNull();
    });

    it('should validate email correctly', () => {
      expect(validateField('invalid-email', authValidationRules.email)).toBe('Invalid format');
      expect(validateField('valid@email.com', authValidationRules.email)).toBeNull();
    });

    it('should validate password correctly', () => {
      expect(validateField('weak', authValidationRules.password)).toBe('Must be at least 8 characters');
      expect(validateField('nouppercase123', authValidationRules.password)).toBe('Password must contain at least one uppercase letter');
      expect(validateField('NOLOWERCASE123', authValidationRules.password)).toBe('Password must contain at least one lowercase letter');
      expect(validateField('NoNumbers', authValidationRules.password)).toBe('Password must contain at least one number');
      expect(validateField('ValidPassword123', authValidationRules.password)).toBeNull();
    });

    it('should validate full name correctly', () => {
      const longName = 'a'.repeat(256);
      expect(validateField(longName, authValidationRules.fullName)).toBe('Must be no more than 255 characters');
      expect(validateField('Valid Name', authValidationRules.fullName)).toBeNull();
      expect(validateField('', authValidationRules.fullName)).toBeNull(); // Optional field
    });
  });

  describe('validateConfirmPassword', () => {
    it('should validate password confirmation', () => {
      expect(validateConfirmPassword('password123', '')).toBe('Please confirm your password');
      expect(validateConfirmPassword('password123', 'different123')).toBe('Passwords do not match');
      expect(validateConfirmPassword('password123', 'password123')).toBeNull();
    });
  });
});