import React, { useState } from 'react';
import { 
  Home,
  Users,
  UserCog,
  Handshake,
  BarChart2,
  Package,
  Settings,
  Calendar,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

type MenuItem = {
  id: string;
  icon: React.ElementType;
  label: string;
};

const menuItems: MenuItem[] = [
  { id: 'home', icon: Home, label: 'Home' },
  { id: 'beneficiaire', icon: Users, label: 'Beneficiaires' },
  { id: 'benevole', icon: UserCog, label: 'Bénévoles' },
  { id: 'partenaires', icon: Handshake, label: 'Partenaires' },
  { id: 'calendrier', icon: Calendar, label: 'Calendrier' },
  { id: 'analyses', icon: BarChart2, label: 'Analyses' },
  { id: 'stock', icon: Package, label: 'Stock' },
];

interface SidebarProps {
  onMenuSelect: (menuId: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ onMenuSelect }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div 
      className={`sticky top-0 h-screen bg-gray-800 text-white transition-all duration-300 flex flex-col
        ${isCollapsed ? 'w-16' : 'w-64'}`}
    >
      <div className="p-4 flex items-center justify-between border-b border-gray-700">
        {!isCollapsed && <h1 className="text-xl font-bold">Association APA30</h1>}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-2 hover:bg-gray-700 rounded-lg"
        >
          {isCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        <nav className="p-2">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onMenuSelect(item.id)}
              className="w-full flex items-center gap-2 p-2 hover:bg-gray-700 rounded-lg mb-1 transition-colors"
            >
              <item.icon size={20} />
              {!isCollapsed && <span>{item.label}</span>}
            </button>
          ))}
        </nav>
      </div>

      <div className="border-t border-gray-700 p-2">
        <button
          onClick={() => onMenuSelect('parametre')}
          className="w-full flex items-center gap-2 p-2 hover:bg-gray-700 rounded-lg transition-colors"
        >
          <Settings size={20} />
          {!isCollapsed && <span>Parametre</span>}
        </button>
      </div>
    </div>
  );
};

export default Sidebar;