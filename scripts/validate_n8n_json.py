#!/usr/bin/env python3
"""
Validador de Workflow n8n JSON para LeadFlow Automation
Verifica estructura, nodos, conexiones y variables

Uso: python validate_n8n_json.py ../leadflow_ai_n8n_workflow.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

class N8NWorkflowValidator:
    """Validador completo de workflows n8n"""
    
    REQUIRED_FIELDS = {'name', 'nodes', 'connections', 'active'}
    REQUIRED_NODE_FIELDS = {'name', 'type', 'typeVersion', 'position', 'parameters'}
    REQUIRED_TRIGGER_TYPES = {'n8n-nodes-base.gmailTrigger', 'n8n-nodes-base.webhook'}
    ERROR_HANDLING_KEYWORDS = {'Error Handling', 'error', 'continueOnFail'}
    
    def __init__(self, json_path: str):
        self.json_path = Path(json_path)
        self.workflow = None
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats = {
            'total_nodes': 0,
            'triggers': 0,
            'ai_nodes': 0,
            'error_handlers': 0,
            'hitl_nodes': 0,
            'connections': 0,
            'variables_found': Set()
        }
    
    def validate(self) -> Tuple[bool, Dict]:
        """Ejecuta validación completa"""
        
        # 1. Cargar JSON
        if not self._load_json():
            return False, self._get_report()
        
        # 2. Validaciones estructurales
        self._validate_structure()
        
        # 3. Validar nodos
        self._validate_nodes()
        
        # 4. Validar conexiones
        self._validate_connections()
        
        # 5. Validar presencia de componentes clave
        self._validate_key_components()
        
        # 6. Validar variables
        self._validate_variables()
        
        success = len(self.errors) == 0
        return success, self._get_report()
    
    def _load_json(self) -> bool:
        """Carga y parsea el JSON"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.workflow = json.load(f)
            return True
        except FileNotFoundError:
            self.errors.append(f"Archivo no encontrado: {self.json_path}")
            return False
        except json.JSONDecodeError as e:
            self.errors.append(f"JSON inválido: {e}")
            return False
    
    def _validate_structure(self):
        """Valida estructura principal"""
        if not isinstance(self.workflow, dict):
            self.errors.append("Raíz del workflow debe ser un objeto JSON")
            return
        
        missing = self.REQUIRED_FIELDS - set(self.workflow.keys())
        if missing:
            self.errors.append(f"Campos requeridos faltantes: {missing}")
        
        if not isinstance(self.workflow.get('nodes'), list):
            self.errors.append("'nodes' debe ser un array")
        
        if not isinstance(self.workflow.get('connections'), dict):
            self.errors.append("'connections' debe ser un objeto")
    
    def _validate_nodes(self):
        """Valida cada nodo del workflow"""
        nodes = self.workflow.get('nodes', [])
        self.stats['total_nodes'] = len(nodes)
        
        node_names = set()
        
        for idx, node in enumerate(nodes):
            # Validar estructura básica
            if not isinstance(node, dict):
                self.errors.append(f"Nodo {idx} debe ser un objeto")
                continue
            
            missing = self.REQUIRED_NODE_FIELDS - set(node.keys())
            if missing:
                self.errors.append(f"Nodo {idx} ({node.get('name')}): campos faltantes {missing}")
            
            # Registrar nombre
            node_name = node.get('name', f'Nodo_{idx}')
            if node_name in node_names:
                self.errors.append(f"Nodo duplicado: {node_name}")
            node_names.add(node_name)
            
            # Clasificar nodos
            node_type = node.get('type', '')
            
            if node_type in self.REQUIRED_TRIGGER_TYPES:
                self.stats['triggers'] += 1
            
            if 'openai' in node_type.lower():
                self.stats['ai_nodes'] += 1
            
            if any(kw in node_name for kw in self.ERROR_HANDLING_KEYWORDS):
                self.stats['error_handlers'] += 1
            
            if 'slack' in node_type.lower() or 'approval' in node_name.lower():
                self.stats['hitl_nodes'] += 1
        
        # Validar triggers
        if self.stats['triggers'] == 0:
            self.errors.append("No se encontró ningún trigger (Gmail o Webhook)")
        
        if self.stats['ai_nodes'] == 0:
            self.errors.append("No se encontró nodo OpenAI para procesamiento IA")
        
        if self.stats['error_handlers'] < 2:
            self.warnings.append(f"Se encontraron {self.stats['error_handlers']} nodos de Error Handling (se requieren al menos 2)")
        
        if self.stats['hitl_nodes'] == 0:
            self.warnings.append("No se encontraron nodos de Human-in-the-Loop (Slack/Aprobación)")
    
    def _validate_connections(self):
        """Valida conexiones entre nodos"""
        connections = self.workflow.get('connections', {})
        self.stats['connections'] = len(connections)
        
        # Obtener todos los nombres de nodos
        node_names = {node.get('name') for node in self.workflow.get('nodes', [])}
        
        for source_node, destinations in connections.items():
            if source_node not in node_names:
                self.errors.append(f"Conexión desde nodo no existente: {source_node}")
            
            if isinstance(destinations, dict):
                for connection_type, targets in destinations.items():
                    if connection_type not in ['main', 'onError']:
                        self.warnings.append(f"Tipo de conexión desconocido: {connection_type}")
                    
                    if isinstance(targets, list):
                        for target_list in targets:
                            for target in target_list:
                                if target.get('node') not in node_names:
                                    self.errors.append(f"Conexión a nodo no existente: {target.get('node')}")
    
    def _validate_key_components(self):
        """Valida presencia de componentes clave"""
        node_names = {node.get('name') for node in self.workflow.get('nodes', [])}
        
        key_components = {
            'Trigger': ['trigger', 'Trigger', 'Gmail', 'Webhook'],
            'Email Parsing': ['Parse', 'parse', 'email'],
            'IA Processing': ['OpenAI', 'openai', 'IA', 'ia'],
            'Airtable Integration': ['Airtable', 'airtable'],
            'HITL': ['Slack', 'slack', 'approval', 'Approval', 'HITL'],
            'Error Handling': ['Error', 'error', 'Handling', 'handling']
        }
        
        for component, keywords in key_components.items():
            found = any(
                any(kw in name for kw in keywords)
                for name in node_names
            )
            if not found:
                self.warnings.append(f"Componente recomendado no encontrado: {component}")
    
    def _validate_variables(self):
        """Extrae y valida variables dinámicas"""
        nodes_json = json.dumps(self.workflow)
        
        # Buscar variables {{$env...}} y {{$node...}}
        import re
        env_vars = set(re.findall(r'\{\{\\$env\.([^}]+)\}\}', nodes_json))
        node_vars = set(re.findall(r'\{\{\\$node\[\"([^\"]+)\"\]', nodes_json))
        
        self.stats['variables_found'] = {
            'env_vars': env_vars,
            'node_refs': node_vars
        }
        
        # Variables de entorno requeridas
        required_env_vars = {
            'AIRTABLE_BASE_ID',
            'GMAIL_MAILBOX',
            'N8N_WEBHOOK_URL',
            'SLACK_CHANNEL_LEADS',
            'MODEL_GPT',
            'MAX_TOKENS_OPENAI'
        }
        
        missing_env = required_env_vars - env_vars
        if missing_env:
            self.warnings.append(f"Variables de entorno recomendadas no configuradas: {missing_env}")
        
        # Verificar que referencias a nodos existan
        node_names = {node.get('name') for node in self.workflow.get('nodes', [])}
        for node_ref in node_vars:
            if node_ref not in node_names:
                self.errors.append(f"Referencia a nodo no existente en variable: {node_ref}")
    
    def _get_report(self) -> Dict:
        """Genera reporte final"""
        return {
            'valid': len(self.errors) == 0,
            'filename': str(self.json_path),
            'workflow_name': self.workflow.get('name', 'N/A') if self.workflow else 'N/A',
            'stats': {
                'total_nodes': self.stats['total_nodes'],
                'triggers': self.stats['triggers'],
                'ai_nodes': self.stats['ai_nodes'],
                'error_handlers': self.stats['error_handlers'],
                'hitl_nodes': self.stats['hitl_nodes'],
                'total_connections': self.stats['connections'],
                'environment_variables': list(self.stats['variables_found'].get('env_vars', [])),
                'node_references': list(self.stats['variables_found'].get('node_refs', []))
            },
            'errors': self.errors,
            'warnings': self.warnings
        }

def main():
    if len(sys.argv) < 2:
        print("Uso: python validate_n8n_json.py <ruta_al_workflow.json>")
        sys.exit(1)
    
    json_path = sys.argv[1]
    validator = N8NWorkflowValidator(json_path)
    
    print("\n" + "="*80)
    print("VALIDADOR DE WORKFLOW n8n - LeadFlow Automation")
    print("="*80)
    
    valid, report = validator.validate()
    
    # Mostrar información general
    print(f"\n📋 Workflow: {report['workflow_name']}")
    print(f"📁 Archivo: {report['filename']}")
    
    # Mostrar estadísticas
    stats = report['stats']
    print(f"\n📊 ESTADÍSTICAS:")
    print(f"   • Nodos totales: {stats['total_nodes']}")
    print(f"   • Triggers: {stats['triggers']}")
    print(f"   • Nodos IA: {stats['ai_nodes']}")
    print(f"   • Error Handlers: {stats['error_handlers']}")
    print(f"   • Nodos HITL: {stats['hitl_nodes']}")
    print(f"   • Conexiones: {stats['total_connections']}")
    print(f"   • Variables de entorno: {len(stats['environment_variables'])}")
    print(f"   • Referencias a nodos: {len(stats['node_references'])}")
    
    # Mostrar errores
    if report['errors']:
        print(f"\n❌ ERRORES ({len(report['errors'])}):")
        for error in report['errors']:
            print(f"   • {error}")
    
    # Mostrar warnings
    if report['warnings']:
        print(f"\n⚠️  ADVERTENCIAS ({len(report['warnings'])}):")
        for warning in report['warnings']:
            print(f"   • {warning}")
    
    # Resultado final
    print(f"\n{'✅ VALIDACIÓN EXITOSA' if valid else '❌ VALIDACIÓN FALLIDA'}")
    print("="*80 + "\n")
    
    sys.exit(0 if valid else 1)

if __name__ == '__main__':
    main()
