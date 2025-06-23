
import { Lightbulb, Mic } from 'lucide-react';
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
    <Sidebar className="border-r border-gray-200 w-80">
      <SidebarHeader className="border-b border-gray-200 p-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">K</span>
          </div>
          <span className="font-semibold text-gray-900 text-xl">Kreate</span>
        </div>
      </SidebarHeader>
      
      <SidebarContent className="p-4">
        <SidebarGroup>
          <SidebarGroupLabel className="text-sm font-medium text-gray-500 mb-3">Tools</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-2">
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    onClick={() => handleNavigation(item.url, item.isComingSoon)}
                    className={`
                      w-full flex items-center gap-3 px-3 py-3 rounded-lg text-left transition-colors
                      ${location.pathname === item.url && !item.isComingSoon 
                        ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' 
                        : 'text-gray-700 hover:bg-gray-50'
                      }
                      ${item.isComingSoon ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50'}
                    `}
                    disabled={item.isComingSoon}
                  >
                    <item.icon className="w-5 h-5 flex-shrink-0" />
                    <span className="font-medium">{item.title}</span>
                    {item.isComingSoon && (
                      <span className="ml-auto text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded-full">Soon</span>
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
