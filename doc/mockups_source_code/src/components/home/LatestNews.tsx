import React from 'react';
import { Bell } from 'lucide-react';

interface NewsItem {
  id: number;
  title: string;
  date: string;
  category: string;
  priority: 'high' | 'medium' | 'low';
}

const news: NewsItem[] = [
  {
    id: 1,
    title: "Distribution alimentaire exceptionnelle prévue ce weekend",
    date: "2024-03-19",
    category: "Événement",
    priority: "high"
  },
  {
    id: 2,
    title: "Nouveau partenariat avec la banque alimentaire",
    date: "2024-03-18",
    category: "Partenariat",
    priority: "medium"
  },
  {
    id: 3,
    title: "Formation des bénévoles le mois prochain",
    date: "2024-03-17",
    category: "Formation",
    priority: "low"
  }
];

const priorityColors = {
  high: "bg-red-100 text-red-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-green-100 text-green-800"
};

const LatestNews: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Dernières Nouvelles</h2>
        <Bell className="text-yellow-600" />
      </div>
      <div className="space-y-4">
        {news.map((item) => (
          <div key={item.id} className="border-b border-gray-100 last:border-0 pb-3 last:pb-0">
            <div className="flex items-center justify-between mb-2">
              <span className={`px-2 py-1 rounded-full text-xs ${priorityColors[item.priority]}`}>
                {item.category}
              </span>
              <span className="text-sm text-gray-500">
                {new Date(item.date).toLocaleDateString('fr-FR')}
              </span>
            </div>
            <p className="text-gray-800">{item.title}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LatestNews;