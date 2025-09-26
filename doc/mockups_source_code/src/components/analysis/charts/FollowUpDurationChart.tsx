import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface Props {
  className?: string;
}

const generateHistogramData = () => {
  const data = [];
  const intervals = [
    '0-6', '7-12', '13-24', '25-36', '37-48', 
    '49-60', '61-72', '73-84', '85-96', '97+'
  ];
  
  // Generate mock data with a normal-like distribution
  const counts = [15, 25, 35, 45, 38, 30, 20, 12, 8, 5];
  
  intervals.forEach((interval, index) => {
    data.push({
      interval,
      count: counts[index]
    });
  });
  
  return data;
};

const FollowUpDurationChart: React.FC<Props> = ({ className = '' }) => {
  const data = generateHistogramData();

  return (
    <div className={`bg-white p-6 rounded-lg shadow-sm ${className}`}>
      <h2 className="text-lg font-semibold mb-4">Durée de Suivi des Bénéficiaires (en mois)</h2>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="interval" 
              label={{ 
                value: 'Durée (mois)', 
                position: 'bottom', 
                offset: 0 
              }}
            />
            <YAxis
              label={{ 
                value: 'Nombre de bénéficiaires', 
                angle: -90, 
                position: 'insideLeft',
                offset: 10
              }}
            />
            <Tooltip />
            <Bar dataKey="count" fill="#6366F1" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default FollowUpDurationChart;