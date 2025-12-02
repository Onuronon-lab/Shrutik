import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  MicrophoneIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  ArrowDownTrayIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { ThemeToggle } from './ThemeSwitcher';
import LanguageSwitch from './LanguageSwitch';
// import logo from '../../assets/shrutik_logo.png';

const Navbar: React.FC = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navigationItems = [
    {
      name: 'Record Voice',
      href: '/record',
      icon: MicrophoneIcon,
      roles: ['contributor', 'admin', 'sworik_developer'],
    },
    {
      name: 'Transcribe',
      href: '/transcribe',
      icon: DocumentTextIcon,
      roles: ['contributor', 'admin', 'sworik_developer'],
    },
    {
      name: 'Export Data',
      href: '/export',
      icon: ArrowDownTrayIcon,
      roles: ['admin', 'sworik_developer'],
    },
    {
      name: 'Admin',
      href: '/admin',
      icon: Cog6ToothIcon,
      roles: ['admin'],
    },
  ];

  const filteredNavItems = navigationItems.filter(item => !user || item.roles.includes(user.role));

  if (!isAuthenticated) {
    return (
      <nav className="bg-background shadow-sm border-b border-border">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center space-x-2">
              <MicrophoneIcon className="h-8 w-8 text-primary" />
              <span className="text-xl font-bold text-foreground">Shrutik</span>
            </Link>
            <Link
              to="/login"
              className="bg-primary hover:bg-primary-hover text-primary-foreground px-4 py-2 rounded-md text-sm font-medium transition-colors"
            >
              Sign In
            </Link>
          </div>
        </div>
      </nav>
    );
  }

  return (
    <nav className="bg-background shadow-sm border-b border-border">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            {/* <img src={logo} className="h-40 w-96 bg-white" srcSet="shrutik_logo" alt="" /> */}
            <MicrophoneIcon className="h-8 w-8 text-primary" />
            <span className="text-xl font-bold text-foreground">Shrutik</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {filteredNavItems.map(item => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className="flex items-center space-x-1 text-foreground hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </div>

          {/* User Menu */}
          <div className="hidden md:flex items-center space-x-4">
            <ThemeToggle />
            <div className="text-sm text-secondary-foreground">
              <span className="font-medium">{user?.name}</span>
            </div>
            <LanguageSwitch />
            <button
              onClick={handleLogout}
              className="flex items-center space-x-1 text-destructive hover:text-destructive-hover px-3 py-2 rounded-md text-sm font-medium transition-colors border border-destructive hover:border-destructive-hover"
            >
              <ArrowRightOnRectangleIcon className="h-4 w-4" />
              <span>Logout</span>
            </button>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <ThemeToggle className="mr-1 h-8 w-16 px-1" />
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="text-foreground hover:text-foreground p-2"
            >
              {isMobileMenuOpen ? (
                <XMarkIcon className="h-6 w-6" />
              ) : (
                <Bars3Icon className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t border-border py-4">
            <div className="space-y-2">
              {filteredNavItems.map(item => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className="flex items-center space-x-2 text-mutud hover:text-primary px-3 py-2 rounded-md text-base font-medium transition-colors"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <Icon className="h-5 w-5" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
              <div className="border-t border-border pt-4 mt-4">
                <div className="px-3 py-2 text-sm">
                  <div className="font-medium">{user?.name}</div>
                  <div className="text-foreground">{user?.email}</div>
                  <span className="inline-block mt-1 px-2 py-1 bg-muted text-secondary-foreground rounded-full text-xs">
                    {user?.role}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-2 text-destructive hover:text-destructive-hover px-3 py-2 rounded-md text-base font-medium transition-colors w-full text-left"
                >
                  <ArrowRightOnRectangleIcon className="h-5 w-5" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
