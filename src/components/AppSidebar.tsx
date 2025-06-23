
import { Lightbulb, Mic, Plus } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from './ui/sidebar';

const menuItems = [
  {
    title: 'Ideate',
    icon: Lightbulb,
    url: '#',
    isComingSoon: true,
  },
  {
    title: 'Dub',
    icon: Mic,
    url: '/',
    isComingSoon: false,
  },
];

export function AppSidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleNavigation = (url: string, isComingSoon: boolean) => {
    if (!isComingSoon) {
      navigate(url);
    }
  };

  return (
    <Sidebar className="border-r border-gray-200">
      <SidebarHeader className="border-b border-gray-200 p-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">K</span>
          </div>
          <span className="font-semibold text-gray-900">Kreate</span>
        </div>
      </SidebarHeader>
      
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Tools</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    onClick={() => handleNavigation(item.url, item.isComingSoon)}
                    className={`
                      ${location.pathname === item.url && !item.isComingSoon ? 'bg-gray-100 text-gray-900' : 'text-gray-700'}
                      ${item.isComingSoon ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50'}
                    `}
                    disabled={item.isComingSoon}
                  >
                    <item.icon className="w-4 h-4" />
                    <span>{item.title}</span>
                    {item.isComingSoon && (
                      <span className="ml-auto text-xs text-gray-400">Soon</span>
                    )}
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
