import React from 'react';
import { CalendarDays, Phone, Users, Plus } from 'lucide-react';

interface Change {
  type: string;
  description: string;
}

interface Interaction {
  id: number;
  date: string;
  type: 'association' | 'external' | 'phone';
  title: string;
  description: string;
  changes: Change[];
}

const mockInteractions: Interaction[] = [
  {
    id: 1,
    date: '2024-03-20',
    type: 'association',
    title: 'Demande de vestiaire',
    description: "Le bénéficiaire exprime un besoin urgent en vêtements d'hiver pour ses enfants. La situation financière actuelle ne permet pas l'achat de nouveaux vêtements.",
    changes: [
      { type: 'service', description: 'Service vestiaire social activé' },
      { type: 'expense', description: 'Nouvelle charge: Participation vestiaire 5€' }
    ]
  },
  {
    id: 2,
    date: '2024-03-15',
    type: 'phone',
    title: 'Changement situation professionnelle',
    description: "Notification d'un nouveau contrat CDD de 6 mois comme agent d'entretien. 20h/semaine, salaire prévu 800€ net mensuel.",
    changes: [
      { type: 'income', description: 'Nouveau revenu: Salaire +800€' },
      { type: 'income', description: 'RSA diminué de 200€' },
      { type: 'income', description: "Prime d'activité +200€" }
    ]
  },
  {
    id: 3,
    date: '2024-03-10',
    type: 'external',
    title: 'Visite à domicile',
    description: "Évaluation des conditions de logement. Problèmes d'humidité constatés dans la chambre des enfants. Facture d'électricité en hausse due au chauffage d'appoint.",
    changes: [
      { type: 'expense', description: 'Charge électricité augmentée de 45€' },
      { type: 'service', description: 'Demande aide exceptionnelle CCAS initiée' }
    ]
  }
];

const InteractionTimeline: React.FC = () => {
  const getIcon = (type: Interaction['type']) => {
    switch (type) {
      case 'association':
        return <Users className="text-indigo-600" />;
      case 'external':
        return <CalendarDays className="text-green-600" />;
      case 'phone':
        return <Phone className="text-blue-600" />;
    }
  };

  const getTypeLabel = (type: Interaction['type']) => {
    switch (type) {
      case 'association':
        return 'Entretien à l\'association';
      case 'external':
        return 'Entretien externe';
      case 'phone':
        return 'Entretien téléphonique';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold">Dernières Interactions</h2>
        <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2">
          <Plus size={20} />
          Nouvelle Interaction
        </button>
      </div>
      {mockInteractions.map((interaction) => (
        <div key={interaction.id} className="bg-white rounded-lg shadow-sm p-4">
          <div className="flex items-start gap-3">
            <div className="mt-1">{getIcon(interaction.type)}</div>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-500">
                  {new Date(interaction.date).toLocaleDateString('fr-FR')}
                </span>
                <span className="text-sm font-medium text-gray-600">
                  {getTypeLabel(interaction.type)}
                </span>
              </div>
              <h3 className="font-medium text-gray-900 mb-2">{interaction.title}</h3>
              <p className="text-sm text-gray-600 mb-3">{interaction.description}</p>
              {interaction.changes.length > 0 && (
                <div className="border-t border-gray-100 pt-2 mt-2">
                  <p className="text-xs text-gray-500 mb-1">Changements apportés:</p>
                  <ul className="space-y-1">
                    {interaction.changes.map((change, index) => (
                      <li key={index} className="text-sm text-gray-500">
                        {change.description}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default InteractionTimeline;