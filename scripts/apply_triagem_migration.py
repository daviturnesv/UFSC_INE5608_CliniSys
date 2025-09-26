"""
Script temporário para aplicar a migração de triagem manualmente
"""
import asyncio
import sys
from pathlib import Path

# Adicionar o projeto ao path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.backend.db.database import AsyncSessionLocal, engine
from sqlalchemy import text


async def apply_triagem_migration():
    """Aplica as mudanças de triagem diretamente no banco"""
    
    async with engine.begin() as conn:
        # Verificar se a tabela já existe
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='registros_triagem'")
        )
        
        if result.fetchone():
            print("✅ Tabela registros_triagem já existe")
            return
        
        print("🔧 Criando tabela registros_triagem...")
        
        # Criar tabela registros_triagem
        await conn.execute(text("""
            CREATE TABLE registros_triagem (
                id INTEGER NOT NULL PRIMARY KEY,
                paciente_id INTEGER NOT NULL,
                aluno_id INTEGER,
                prioridade VARCHAR(20),
                situacao VARCHAR(20) NOT NULL DEFAULT 'AGUARDANDO',
                queixa_principal VARCHAR(500),
                sinais_vitais TEXT,
                observacoes TEXT,
                necessidades_identificadas TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                triagem_iniciada_em TIMESTAMP,
                triagem_concluida_em TIMESTAMP,
                
                FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE,
                FOREIGN KEY(aluno_id) REFERENCES usuarios(id) ON DELETE SET NULL
            )
        """))
        
        # Criar índices
        await conn.execute(text("CREATE INDEX ix_registros_triagem_paciente_id ON registros_triagem(paciente_id)"))
        await conn.execute(text("CREATE INDEX ix_registros_triagem_aluno_id ON registros_triagem(aluno_id)"))
        await conn.execute(text("CREATE INDEX ix_registros_triagem_prioridade ON registros_triagem(prioridade)"))
        await conn.execute(text("CREATE INDEX ix_registros_triagem_situacao ON registros_triagem(situacao)"))
        
        print("✅ Tabela registros_triagem criada com sucesso!")


if __name__ == "__main__":
    asyncio.run(apply_triagem_migration())