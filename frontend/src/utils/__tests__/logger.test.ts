/**
 * Logger utility tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { logger } from '../logger';

describe('Logger Utility', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks();
  });

  it('should log info messages', () => {
    const consoleSpy = vi.spyOn(console, 'info').mockImplementation(() => {});
    
    logger.info('Test info message');
    
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('[INFO]'),
      expect.stringContaining('Test info message')
    );
    
    consoleSpy.mockRestore();
  });

  it('should log error messages', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    logger.error('Test error message');
    
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('[ERROR]'),
      expect.stringContaining('Test error message')
    );
    
    consoleSpy.mockRestore();
  });

  it('should log warn messages', () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    
    logger.warn('Test warning message');
    
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('[WARN]'),
      expect.stringContaining('Test warning message')
    );
    
    consoleSpy.mockRestore();
  });

  it('should log debug messages', () => {
    const consoleSpy = vi.spyOn(console, 'debug').mockImplementation(() => {});
    
    logger.debug('Test debug message');
    
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('[DEBUG]'),
      expect.stringContaining('Test debug message')
    );
    
    consoleSpy.mockRestore();
  });

  it('should handle different log levels', () => {
    const consoleSpy = vi.spyOn(console, 'info').mockImplementation(() => {});
    
    // Test that logger exists and has the expected methods
    expect(typeof logger.info).toBe('function');
    expect(typeof logger.error).toBe('function');
    expect(typeof logger.warn).toBe('function');
    expect(typeof logger.debug).toBe('function');
    
    consoleSpy.mockRestore();
  });

  it('should format messages with timestamps', () => {
    const consoleSpy = vi.spyOn(console, 'info').mockImplementation(() => {});
    
    logger.info('Timestamp test');
    
    // Check that the log includes a timestamp pattern
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringMatching(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/),
      expect.stringContaining('Timestamp test')
    );
    
    consoleSpy.mockRestore();
  });
});