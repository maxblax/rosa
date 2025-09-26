export interface Event {
  id: string;
  beneficiaryId: string;
  title: string;
  start: Date;
  end: Date;
  type: 'rendez-vous' | 'permanence';
}

export interface Beneficiary {
  id: string;
  name: string;
}

export type ViewType = 'week' | 'month';