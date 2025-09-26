import React from 'react';
import { User } from 'lucide-react';

const UserProfile: React.FC = () => {
  return (
    <div className="flex items-center gap-3 p-4 bg-white shadow-sm">
      <div className="flex items-center gap-2">
        <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
          <User className="text-indigo-600" size={20} />
        </div>
        <div>
          <h3 className="font-medium text-gray-800">Marie Orcel</h3>
          <p className="text-sm text-gray-500">Assistante Sociale</p>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;